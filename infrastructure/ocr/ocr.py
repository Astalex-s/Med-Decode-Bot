import os

import cv2
import numpy as np
import fitz  # PyMuPDF
import easyocr

from domain.interfaces.ocr_service import IOCRService


def _preprocess(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


class OCRService(IOCRService):

    def __init__(self):
        # Инициализируем ридер один раз при создании сервиса
        self._reader = easyocr.Reader(['ru', 'en'], gpu=False)

    def extract_text(self, file_path: str) -> str:
        text = ""
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()

        if ext == "pdf":
            doc = fitz.open(file_path)
            for page in doc:
                pix = page.get_pixmap()
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                img = _preprocess(img)
                for item in self._reader.readtext(img):
                    text += item[1] + "\n"
        else:
            img = cv2.imread(file_path)
            img = _preprocess(img)
            for item in self._reader.readtext(img):
                text += item[1] + "\n"

        return text
