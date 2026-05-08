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
COLOR_PRIMARY = (41, 98, 255)       # синий — заголовки секций
COLOR_ACCENT = (230, 240, 255)      # светло-синий фон
COLOR_TEXT = (33, 37, 41)           # почти чёрный
COLOR_MUTED = (108, 117, 125)      # серый

COLOR_NORMAL = (25, 118, 210)      # синий — в норме
COLOR_NORMAL_BG = (227, 242, 253)  # светло-синий фон подзаголовка
COLOR_ABNORMAL = (198, 40, 40)     # красный — отклонение
COLOR_ABNORMAL_BG = (255, 235, 238)  # светло-красный фон подзаголовка

COLOR_TABLE_HEADER = (41, 98, 255)
COLOR_TABLE_HEADER_TEXT = (255, 255, 255)
COLOR_TABLE_ROW_EVEN = (245, 248, 255)
COLOR_TABLE_ROW_ODD = (255, 255, 255)
COLOR_TABLE_BORDER = (200, 210, 230)

SECTION_COLORS = {
    "СЧИТАННЫЕ ДАННЫЕ": (232, 245, 233),
    "ПОДРОБНЫЙ РАЗБОР": (227, 242, 253),
    "ОБЩАЯ ОЦЕНКА": (243, 229, 245),
    "РЕКОМЕНДАЦИИ": (255, 243, 224),
    "ДИСКЛЕЙМЕР": (255, 243, 205),
}

# Маркеры статуса
_NORMAL_MARKERS = ("норма",)
_ABNORMAL_MARKERS = ("выше нормы", "ниже нормы", "повышен", "понижен", "снижен",
                     "увеличен", "отклонение", "выше референс", "ниже референс")


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


def _detect_status(text: str) -> str:
    """Определяет статус по тексту: 'normal', 'abnormal' или 'unknown'."""
    lower = text.lower()
    for marker in _ABNORMAL_MARKERS:
        if marker in lower:
            return "abnormal"
    for marker in _NORMAL_MARKERS:
        if marker in lower:
            return "normal"
    return "unknown"


def _is_table_line(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def _is_separator_line(line: str) -> bool:
    return bool(re.match(r"^\s*\|[\s\-:|]+\|\s*$", line))


def _parse_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _strip_markdown_hashes(line: str) -> str:
    """Убирает #### / ### / ## / # из начала строки."""
    return re.sub(r"^#{1,6}\s*", "", line)


def _strip_bold_markers(text: str) -> str:
    """Убирает ** из текста."""
    return text.replace("**", "")


class MedDecodePDF(FPDF):
    def __init__(self, font_regular: str, font_bold: str):
        super().__init__()
        self._font_regular = font_regular
        self._font_bold = font_bold
        self.add_font("DejaVu", "", font_regular)
        self.add_font("DejaVu", "B", font_bold)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
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
        # Заголовок секции
        self.set_fill_color(*COLOR_PRIMARY)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_x(10)
        self.cell(190, 9, f"  {number}. {title}", fill=True)
        self.ln(11)
        self.set_text_color(*COLOR_TEXT)

        # Содержимое
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Пустая строка
            if not stripped:
                self.ln(2)
                i += 1
                continue

            # Таблица — собираем все строки таблицы
            if _is_table_line(stripped):
                table_lines = []
                while i < len(lines) and _is_table_line(lines[i].strip()):
                    if not _is_separator_line(lines[i]):
                        table_lines.append(_parse_table_row(lines[i]))
                    i += 1
                if table_lines:
                    self._render_table(table_lines)
                continue

            # Подзаголовок (#### или ### или ##)
            if stripped.startswith("#"):
                subheading = _strip_markdown_hashes(stripped)
                subheading = _strip_bold_markers(subheading)
                # Определяем статус: смотрим вперёд до следующего подзаголовка
                lookahead = ""
                for j in range(i + 1, min(i + 20, len(lines))):
                    if lines[j].strip().startswith("#"):
                        break
                    lookahead += lines[j] + "\n"
                status = _detect_status(lookahead)
                self._render_subheading(subheading, status)
                i += 1
                continue

            # Обычная строка
            self._render_line(stripped, 14, 182)
            i += 1

        self.ln(4)

    def _render_table(self, rows: list[list[str]]):
        """Рендерит таблицу с шапкой и чередующимися строками."""
        if not rows:
            return

        if self.get_y() > 240:
            self.add_page()

        n_cols = len(rows[0])
        # Ширины колонок: первая шире (название), остальные равные
        available_w = 186
        if n_cols == 1:
            col_widths = [available_w]
        elif n_cols == 2:
            col_widths = [120, 66]
        elif n_cols == 3:
            col_widths = [90, 48, 48]
        else:
            first_w = 80
            rest_w = (available_w - first_w) / max(n_cols - 1, 1)
            col_widths = [first_w] + [rest_w] * (n_cols - 1)

        x_start = 12
        row_h = 7

        # Шапка
        header = rows[0]
        self.set_fill_color(*COLOR_TABLE_HEADER)
        self.set_text_color(*COLOR_TABLE_HEADER_TEXT)
        self.set_font("DejaVu", "B", 8)
        self.set_x(x_start)
        for c, w in zip(header, col_widths):
            self.cell(w, row_h, f" {_strip_bold_markers(c)}", border=1, fill=True)
        self.ln(row_h)

        # Данные
        self.set_text_color(*COLOR_TEXT)
        self.set_font("DejaVu", "", 8)
        for row_idx, row in enumerate(rows[1:]):
            if self.get_y() > 270:
                self.add_page()

            bg = COLOR_TABLE_ROW_EVEN if row_idx % 2 == 0 else COLOR_TABLE_ROW_ODD
            self.set_fill_color(*bg)

            # Определяем статус строки для цвета текста
            row_text = " ".join(row)
            status = _detect_status(row_text)

            self.set_x(x_start)
            for c_idx, (c, w) in enumerate(zip(row, col_widths)):
                cell_text = _strip_bold_markers(c)
                # Первая колонка всегда обычным цветом
                if c_idx == 0:
                    self.set_text_color(*COLOR_TEXT)
                elif status == "abnormal":
                    self.set_text_color(*COLOR_ABNORMAL)
                elif status == "normal":
                    self.set_text_color(*COLOR_NORMAL)
                else:
                    self.set_text_color(*COLOR_TEXT)

                self.set_draw_color(*COLOR_TABLE_BORDER)
                self.cell(w, row_h, f" {cell_text}", border=1, fill=True)
            self.ln(row_h)

        self.set_text_color(*COLOR_TEXT)
        self.ln(3)

    def _render_subheading(self, text: str, status: str = "unknown"):
        """Рендерит подзаголовок с цветом в зависимости от статуса."""
        if self.get_y() > 250:
            self.add_page()

        if status == "abnormal":
            bg = COLOR_ABNORMAL_BG
            text_color = COLOR_ABNORMAL
        elif status == "normal":
            bg = COLOR_NORMAL_BG
            text_color = COLOR_NORMAL
        else:
            bg = COLOR_NORMAL_BG
            text_color = COLOR_NORMAL

        self.set_fill_color(*bg)
        self.set_text_color(*text_color)
        self.set_font("DejaVu", "B", 9)
        self.set_x(12)
        self.cell(186, 7, f"  {text}", fill=True)
        self.ln(8)
        self.set_text_color(*COLOR_TEXT)

    def _render_line(self, line: str, x: float, w: float):
        """Рендерит строку, поддерживая **жирный** текст, маркеры списка и статус."""
        # Убираем #### если осталось
        line = _strip_markdown_hashes(line)

        # Маркер списка
        bullet = ""
        if line.startswith(("- ", "• ", "* ")):
            bullet = "  "
            line = line[2:].strip()
        elif re.match(r"^\d+\.\s", line):
            m = re.match(r"^(\d+\.\s)", line)
            bullet = m.group(1)
            line = line[m.end():]

        if bullet:
            self.set_x(x)
            self.set_font("DejaVu", "", 9)
            self.cell(5, 5, bullet)
            x += 5
            w -= 5

        # Определяем статус строки для подсветки ключевых слов
        status = _detect_status(line)

        # Проверяем, есть ли строка "Статус:" — подсвечиваем значение
        if re.search(r"статус", line, re.IGNORECASE):
            self._render_status_line(line, x, w, status)
            return

        # Парсим **bold** фрагменты
        parts = re.split(r"(\*\*[^*]+\*\*)", line)
        if len(parts) == 1:
            self.set_x(x)
            self.set_font("DejaVu", "", 9)
            self.multi_cell(w, 5, line)
        else:
            self.set_x(x)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    self.set_font("DejaVu", "B", 9)
                    self.write(5, part[2:-2])
                else:
                    self.set_font("DejaVu", "", 9)
                    self.write(5, part)
            self.ln(5)

    def _render_status_line(self, line: str, x: float, w: float, status: str):
        """Рендерит строку со статусом с цветовой подсветкой."""
        # Разбиваем по "Статус:"
        parts = re.split(r"(\*\*[^*]+\*\*)", line)
        self.set_x(x)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                inner = part[2:-2]
                # Проверяем статус внутри bold-фрагмента
                inner_status = _detect_status(inner)
                if inner_status == "abnormal":
                    self.set_text_color(*COLOR_ABNORMAL)
                elif inner_status == "normal":
                    self.set_text_color(*COLOR_NORMAL)
                self.set_font("DejaVu", "B", 9)
                self.write(5, inner)
                self.set_text_color(*COLOR_TEXT)
            else:
                self.set_font("DejaVu", "", 9)
                self.write(5, part)
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

    # Убираем HTML-теги если остались
    analysis_text = re.sub(r"<[^>]+>", "", analysis_text)

    pdf = MedDecodePDF(font_regular, font_bold)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Метаданные
    date_str = generated_at.strftime("%d.%m.%Y %H:%M")
    pdf.add_meta_block(date_str)

    # Секции
    sections = _parse_sections(analysis_text)
    for i, (title, content) in enumerate(sections, start=1):
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.add_section(i, title, content)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
