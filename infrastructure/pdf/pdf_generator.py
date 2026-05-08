import io
import logging
import os
import re
from datetime import datetime

from fpdf import FPDF

logger = logging.getLogger(__name__)

# Пути к шрифтам с поддержкой кириллицы
_FONT_CANDIDATES = {
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ],
}

# Цветовая схема
COLOR_PRIMARY = (41, 98, 255)      # синий
COLOR_ACCENT = (230, 240, 255)     # светло-синий фон
COLOR_WARN = (255, 243, 205)       # жёлтый фон для дисклеймера
COLOR_WARN_BORDER = (255, 193, 7)  # жёлтая рамка
COLOR_TEXT = (33, 37, 41)         # почти чёрный
COLOR_MUTED = (108, 117, 125)     # серый

SECTION_COLORS = {
    "СЧИТАННЫЕ ДАННЫЕ": (232, 245, 233),
    "ПОДРОБНЫЙ РАЗБОР": (227, 242, 253),
    "ОБЩАЯ ОЦЕНКА": (243, 229, 245),
    "РЕКОМЕНДАЦИИ": (255, 243, 224),
    "ДИСКЛЕЙМЕР": (255, 243, 205),
}


def _find_font(kind: str) -> str | None:
    for path in _FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            return path
    return None


def _parse_sections(text: str) -> list[tuple[str, str]]:
    """Разбивает текст GPT на секции вида (заголовок, содержимое)."""
    pattern = re.compile(r"^\s*\d+\.\s+([A-ZА-ЯЁ][A-ZА-ЯЁ\s]+?)[\n\r]", re.MULTILINE)
    matches = list(pattern.finditer(text))

    sections = []
    if not matches:
        return [("РАСШИФРОВКА", text.strip())]

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append((title, content))

    return sections


def _get_section_bg(title: str) -> tuple[int, int, int]:
    for key, color in SECTION_COLORS.items():
        if key in title.upper():
            return color
    return COLOR_ACCENT


class MedDecodePDF(FPDF):
    def __init__(self, font_regular: str, font_bold: str):
        super().__init__()
        self._font_regular = font_regular
        self._font_bold = font_bold
        self.add_font("DejaVu", "", font_regular)
        self.add_font("DejaVu", "B", font_bold)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Синяя полоса сверху
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, 210, 14, "F")
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_y(3)
        self.cell(0, 8, "MedDecode — Расшифровка медицинских анализов", align="C")
        self.ln(14)
        self.set_text_color(*COLOR_TEXT)

    def footer(self):
        self.set_y(-14)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 6, f"Страница {self.page_no()} из {{nb}}", align="C")
        self.set_text_color(*COLOR_TEXT)

    def add_meta_block(self, generated_at: str):
        self.set_fill_color(*COLOR_ACCENT)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.4)
        self.rect(10, self.get_y(), 190, 14, "FD")
        self.set_font("DejaVu", "", 9)
        self.set_text_color(*COLOR_MUTED)
        self.set_x(14)
        self.cell(0, 14, f"Дата формирования отчёта: {generated_at}", align="L")
        self.ln(18)
        self.set_text_color(*COLOR_TEXT)

    def add_section(self, number: int, title: str, content: str):
        bg = _get_section_bg(title)
        # Заголовок секции
        self.set_fill_color(*COLOR_PRIMARY)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_x(10)
        self.cell(190, 9, f"  {number}. {title}", fill=True)
        self.ln(11)
        self.set_text_color(*COLOR_TEXT)

        # Содержимое секции с фоном
        self.set_fill_color(*bg)
        lines = content.split("\n")
        x_start = 10
        w = 190
        y_start = self.get_y()

        # Запоминаем позицию для рисования фона после рендера текста
        self.set_x(x_start + 4)
        for line in lines:
            line = line.strip()
            if not line:
                self.ln(3)
                continue
            self._render_line(line, x_start + 4, w - 8)

        y_end = self.get_y()
        # Рисуем фоновый прямоугольник под текстом
        # (это уже после текста — делаем через multi_cell с rect перед)
        self.ln(4)

    def _render_line(self, line: str, x: float, w: float):
        """Рендерит строку, поддерживая **жирный** текст и маркеры списка."""
        # Маркер списка
        bullet = ""
        if line.startswith(("- ", "• ", "* ")):
            bullet = "• "
            line = line[2:].strip()
        elif re.match(r"^\d+\.\s", line):
            m = re.match(r"^(\d+\.\s)", line)
            bullet = m.group(1)
            line = line[m.end():]

        if bullet:
            self.set_x(x)
            self.set_font("DejaVu", "", 9)
            self.cell(6, 5, bullet)
            x += 6
            w -= 6

        # Парсим **bold** фрагменты
        parts = re.split(r"(\*\*[^*]+\*\*)", line)
        if len(parts) == 1:
            self.set_x(x)
            self.set_font("DejaVu", "", 9)
            self.multi_cell(w, 5, line)
        else:
            # Строка с bold — используем write
            self.set_x(x)
            first = True
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    self.set_font("DejaVu", "B", 9)
                    self.write(5, part[2:-2])
                else:
                    self.set_font("DejaVu", "", 9)
                    self.write(5, part)
                first = False
            self.ln(5)


def generate_report_pdf(analysis_text: str, generated_at: datetime | None = None) -> bytes:
    """Генерирует PDF-отчёт из текста расшифровки. Возвращает байты PDF."""
    if generated_at is None:
        generated_at = datetime.now()

    font_regular = _find_font("regular")
    font_bold = _find_font("bold")

    if not font_regular or not font_bold:
        raise RuntimeError(
            "Не найдены шрифты для PDF. Установите fonts-dejavu-core или укажите пути вручную."
        )

    pdf = MedDecodePDF(font_regular, font_bold)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Метаданные
    date_str = generated_at.strftime("%d.%m.%Y %H:%M")
    pdf.add_meta_block(date_str)

    # Секции
    sections = _parse_sections(analysis_text)
    for i, (title, content) in enumerate(sections, start=1):
        # Если мало места до конца страницы — новая страница
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.add_section(i, title, content)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
