import os
import base64
import logging

import cv2
import numpy as np
import fitz  # PyMuPDF

from domain.interfaces.ocr_service import IOCRService

logger = logging.getLogger(__name__)

MAX_LONG_SIDE = 2048


def _enhance(image: np.ndarray) -> np.ndarray:
    """Лёгкий препроцессинг: контраст + resize. Без бинаризации — Vision работает лучше на натуральных фото."""
    h, w = image.shape[:2]
    long_side = max(h, w)
    if long_side > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / long_side
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    # CLAHE для улучшения контраста
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    return enhanced


def _to_base64(image: np.ndarray) -> str:
    """Конвертирует изображение в base64 строку (JPEG)."""
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buffer).decode('utf-8')


class OCRService(IOCRService):

    def extract_text(self, file_path: str) -> str:
        """Возвращает НЕ текст, а base64 изображений через разделитель для передачи в Vision."""
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()

        if ext == "pdf":
            return self._process_pdf(file_path)
        else:
            return self._process_photo(file_path)

    def _process_photo(self, file_path: str) -> str:
        img = cv2.imread(file_path)
        if img is None:
            logger.error("Не удалось открыть изображение: %s", file_path)
            return ""

        h, w = img.shape[:2]
        logger.info("Фото: %dx%d px, файл: %s", w, h, os.path.basename(file_path))

        enhanced = _enhance(img)
        return _to_base64(enhanced)

    def _process_pdf(self, file_path: str) -> str:
        doc = fitz.open(file_path)
        pages_b64 = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif pix.n == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            enhanced = _enhance(img)
            pages_b64.append(_to_base64(enhanced))
        logger.info("PDF обработан: %d страниц", len(doc))
        # Разделяем страницы специальным маркером
        return "|||PAGE|||".join(pages_b64)
