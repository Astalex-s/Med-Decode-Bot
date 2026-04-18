import os

import cv2
import numpy as np
import fitz  # PyMuPDF — работа с PDF
import easyocr


def preprocess(image):
    # Перевод изображения в чёрно-белый формат
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Улучшение контраста с помощью CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    # Размытие для удаления шума
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    # Бинаризация — чёткое разделение текста и фона
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def extract_text(file_path: str) -> str:
    # Инициализация OCR-ридера с поддержкой русского и английского языков
    ocr = easyocr.Reader(['ru', 'en'], gpu=False)
    text = ""
    if os.path.splitext(file_path)[1].lstrip(".") == "pdf":
        # Открываем PDF и обрабатываем каждую страницу
        doc = fitz.open(file_path)
        for page in doc:
            # Конвертируем страницу в изображение
            pix = page.get_pixmap()
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            # Предобработка изображения
            img = preprocess(img)
            # Распознавание текста
            result = ocr.readtext(img)
            for item in result:
                text += item[1] + '\n'
    else:
        # Читаем изображение (PNG/JPEG)
        img = cv2.imread(file_path)
        # Предобработка изображения
        img = preprocess(img)
        # Распознавание текста
        result = ocr.readtext(img)
        for item in result:
            text += item[1] + '\n'
    return text


if __name__ == "__main__":
    res = extract_text("temp/b9072d58-7b5d-452f-b2d1-590e58a4c0f2.jpg")
    print(res)