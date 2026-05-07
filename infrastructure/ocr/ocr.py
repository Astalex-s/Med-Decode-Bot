import os
import logging

import cv2
import numpy as np
import fitz  # PyMuPDF
import easyocr

from domain.interfaces.ocr_service import IOCRService

logger = logging.getLogger(__name__)

# Минимальная длина длинной стороны для хорошего OCR
MIN_LONG_SIDE = 1800


def _resize_if_needed(image: np.ndarray) -> np.ndarray:
    """Увеличивает изображение если оно слишком маленькое для OCR."""
    h, w = image.shape[:2]
    long_side = max(h, w)
    if long_side < MIN_LONG_SIDE:
        scale = MIN_LONG_SIDE / long_side
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        logger.debug("Изображение увеличено: %dx%d -> %dx%d", w, h, new_w, new_h)
    return image


def _deskew(image: np.ndarray) -> np.ndarray:
    """Корректирует небольшой наклон текста (±15°)."""
    coords = np.column_stack(np.where(image < 128))
    if len(coords) < 50:
        return image
    angle = cv2.minAreaRect(coords.astype(np.float32))[-1]
    # minAreaRect возвращает угол в (-90, 0] — приводим к (-45, 45]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 1.0:   # пренебрежимо малый наклон
        return image
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    logger.debug("Deskew: угол коррекции %.2f°", angle)
    return rotated


def _preprocess_scan(image: np.ndarray) -> np.ndarray:
    """
    Препроцессинг для чистых сканов и PDF-страниц:
    равномерное освещение, нет теней — можно использовать глобальный порог.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def _preprocess_photo(image: np.ndarray) -> np.ndarray:
    """
    Препроцессинг для фотографий с телефона:
    - неравномерное освещение и тени → адаптивный порог
    - возможный наклон → deskew
    - низкое разрешение → upscale
    Возвращает grayscale (не бинарный) — EasyOCR работает на нём лучше для сложных фото.
    """
    image = _resize_if_needed(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Bilateral filter: убирает шум, но сохраняет края символов
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # CLAHE с мелкой сеткой — выравниваем локальный контраст (борьба с тенями)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(6, 6))
    gray = clahe.apply(gray)

    # Адаптивный порог — каждый пиксель сравнивается с локальным окружением
    # Хорошо справляется с неравномерной засветкой и тенями от руки
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,   # размер локального окна (нечётное)
        C=10,           # вычитаем константу — увеличивает контраст текста
    )

    # Лёгкая морфология: закрываем разрывы в тонких символах
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Deskew по бинарному изображению
    binary = _deskew(binary)

    return binary


def _items_to_text(results: list) -> str:
    return "\n".join(item[1] for item in results)


class OCRService(IOCRService):

    def __init__(self):
        self._reader = easyocr.Reader(['ru', 'en'], gpu=False)

    def extract_text(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()

        if ext == "pdf":
            return self._extract_from_pdf(file_path)
        else:
            return self._extract_from_photo(file_path)

    def _extract_from_pdf(self, file_path: str) -> str:
        text = ""
        doc = fitz.open(file_path)
        for page in doc:
            pix = page.get_pixmap(dpi=200)   # повышаем dpi для лучшего OCR
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif pix.n == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            processed = _preprocess_scan(img)
            text += _items_to_text(self._reader.readtext(processed)) + "\n"
        logger.info("PDF OCR завершён: %d страниц", len(doc))
        return text

    def _extract_from_photo(self, file_path: str) -> str:
        img = cv2.imread(file_path)
        if img is None:
            logger.error("Не удалось открыть изображение: %s", file_path)
            return ""

        h, w = img.shape[:2]
        logger.info("OCR фото: %dx%d px, файл: %s", w, h, os.path.basename(file_path))

        processed = _preprocess_photo(img)

        # Прогоняем OCR дважды: на обработанном и оригинальном (после upscale)
        # Берём вариант с большим числом найденных блоков
        results_processed = self._reader.readtext(processed)

        orig_resized = _resize_if_needed(img)
        results_original = self._reader.readtext(orig_resized)

        results = results_processed if len(results_processed) >= len(results_original) else results_original

        logger.info("OCR фото: найдено %d текстовых блоков", len(results))
        return _items_to_text(results)
