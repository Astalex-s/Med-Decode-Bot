"""Генерация PDF документа согласия на обработку персональных данных."""
from fpdf import FPDF

FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD    = "C:/Windows/Fonts/arialbd.ttf"
FONT_ITALIC  = "C:/Windows/Fonts/ariali.ttf"

PAGE_W   = 210   # A4 ширина мм
MARGIN_L = 20
MARGIN_R = 20
TEXT_W   = PAGE_W - MARGIN_L - MARGIN_R   # 170 мм

# Цветовая схема
COLOR_ACCENT  = (41, 98, 171)   # синий
COLOR_SECTION = (240, 245, 255) # светло-голубой фон секций
COLOR_LINE    = (180, 200, 230) # линия разделитель
COLOR_DARK    = (30, 30, 50)    # почти чёрный текст
COLOR_GRAY    = (100, 100, 120)


class ConsentPDF(FPDF):
    def header(self):
        # Синяя полоса сверху
        self.set_fill_color(*COLOR_ACCENT)
        self.rect(0, 0, PAGE_W, 12, "F")
        self.set_font("Arial", "B", 9)
        self.set_text_color(255, 255, 255)
        self.set_xy(MARGIN_L, 3)
        self.cell(TEXT_W, 6, "MedDecode  |  Согласие на обработку персональных данных  |  ФЗ-152 РФ", align="C")
        self.set_text_color(*COLOR_DARK)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.set_text_color(*COLOR_GRAY)
        self.cell(0, 10, f"Страница {self.page_no()}", align="C")
        self.set_text_color(*COLOR_DARK)

    def divider(self):
        self.set_draw_color(*COLOR_LINE)
        self.set_line_width(0.4)
        self.line(MARGIN_L, self.get_y(), PAGE_W - MARGIN_R, self.get_y())
        self.ln(3)

    def section_title(self, text: str):
        self.ln(3)
        # Цветной фон заголовка секции
        y = self.get_y()
        self.set_fill_color(*COLOR_SECTION)
        self.rect(MARGIN_L, y, TEXT_W, 8, "F")
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.6)
        self.line(MARGIN_L, y, MARGIN_L, y + 8)
        self.set_xy(MARGIN_L + 4, y + 1)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*COLOR_ACCENT)
        self.cell(TEXT_W - 4, 6, text)
        self.set_text_color(*COLOR_DARK)
        self.ln(9)

    def body_text(self, text: str):
        self.set_font("Arial", "", 10)
        self.set_x(MARGIN_L)
        self.multi_cell(TEXT_W, 5.5, text)
        self.ln(2)

    def bullet(self, text: str):
        self.set_font("Arial", "", 10)
        bullet_w = 6
        self.set_x(MARGIN_L + 3)
        self.set_font("Arial", "B", 12)
        self.cell(bullet_w, 5.5, chr(8226))   # •
        self.set_font("Arial", "", 10)
        self.multi_cell(TEXT_W - bullet_w - 3, 5.5, text)


def generate_consent_pdf(output_path: str = "consent_document.pdf") -> None:
    pdf = ConsentPDF(format="A4")
    pdf.set_margins(MARGIN_L, 20, MARGIN_R)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("Arial", "",  FONT_REGULAR)
    pdf.add_font("Arial", "B", FONT_BOLD)
    pdf.add_font("Arial", "I", FONT_ITALIC)
    pdf.add_page()

    # ── Заголовок документа ──────────────────────────────────────────────────
    pdf.ln(2)
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(*COLOR_ACCENT)
    pdf.cell(TEXT_W, 10, "Согласие на обработку", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(TEXT_W, 10, "персональных данных", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(TEXT_W, 6, "Федеральный закон от 27.07.2006 № 152-ФЗ «О персональных данных»",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*COLOR_DARK)
    pdf.ln(4)
    pdf.divider()

    # ── Вводная часть ────────────────────────────────────────────────────────
    pdf.body_text(
        "Настоящим я, пользователь сервиса MedDecode (далее — «Сервис»), предоставляю "
        "согласие на обработку своих персональных данных Оператору — владельцу Сервиса "
        "MedDecode (далее — «Оператор»)."
    )

    # ── Секция 1 ─────────────────────────────────────────────────────────────
    pdf.section_title("1.  Состав персональных данных")
    pdf.body_text("Оператор обрабатывает следующие персональные данные:")
    for item in [
        "имя и фамилия (из профиля Telegram);",
        "имя пользователя Telegram (@username);",
        "идентификатор пользователя Telegram (Telegram ID);",
        "изображения и документы, загружаемые пользователем (медицинские анализы и иные документы);",
        "дата и время обращения к Сервису;",
        "информация о подписке и истории использования Сервиса.",
    ]:
        pdf.bullet(item)

    # ── Секция 2 ─────────────────────────────────────────────────────────────
    pdf.section_title("2.  Цели обработки персональных данных")
    pdf.body_text("Персональные данные обрабатываются исключительно в целях:")
    for item in [
        "предоставления функциональных возможностей Сервиса (автоматическое распознавание и расшифровка медицинских анализов);",
        "учёта использования бесплатного лимита и платной подписки;",
        "обеспечения технической поддержки пользователей;",
        "соблюдения требований действующего законодательства Российской Федерации.",
    ]:
        pdf.bullet(item)

    # ── Секция 3 ─────────────────────────────────────────────────────────────
    pdf.section_title("3.  Правовые основания обработки")
    pdf.body_text("Обработка персональных данных осуществляется на основании:")
    for item in [
        "настоящего согласия пользователя (ст. 6, ч. 1, п. 1 ФЗ-152);",
        "необходимости исполнения договора об использовании Сервиса (ст. 6, ч. 1, п. 5 ФЗ-152).",
    ]:
        pdf.bullet(item)

    # ── Секция 4 ─────────────────────────────────────────────────────────────
    pdf.section_title("4.  Перечень действий с персональными данными")
    pdf.body_text(
        "Оператор вправе совершать следующие действия с персональными данными: "
        "сбор, запись, систематизация, накопление, хранение, уточнение (обновление, изменение), "
        "извлечение, использование, передача (предоставление, доступ), блокирование, "
        "удаление, уничтожение персональных данных."
    )

    # ── Секция 5 ─────────────────────────────────────────────────────────────
    pdf.section_title("5.  Передача третьим лицам")
    pdf.body_text(
        "Для обеспечения работы Сервиса персональные данные (текст распознанных документов) "
        "передаются:"
    )
    pdf.bullet(
        "OpenAI (США) — для автоматической интерпретации медицинских данных. "
        "Передача осуществляется в обезличенном виде без идентификационных сведений о пользователе."
    )
    pdf.ln(1)
    pdf.body_text(
        "Оператор не передаёт персональные данные иным третьим лицам без согласия пользователя, "
        "за исключением случаев, предусмотренных законодательством Российской Федерации."
    )

    # ── Секция 6 ─────────────────────────────────────────────────────────────
    pdf.section_title("6.  Срок хранения")
    pdf.body_text(
        "Персональные данные хранятся в течение всего срока использования Сервиса пользователем "
        "и в течение 3 (трёх) лет после прекращения использования, если более длительный срок "
        "не установлен законодательством Российской Федерации."
    )

    # ── Секция 7 ─────────────────────────────────────────────────────────────
    pdf.section_title("7.  Права субъекта персональных данных")
    pdf.body_text("Пользователь вправе:")
    for item in [
        "получить информацию об обработке своих персональных данных;",
        "требовать уточнения, блокирования или уничтожения персональных данных;",
        "отозвать настоящее согласие в любой момент, направив запрос Оператору через интерфейс Сервиса или по контактным данным, указанным ниже.",
    ]:
        pdf.bullet(item)
    pdf.ln(1)
    pdf.body_text(
        "Отзыв согласия не влияет на законность обработки, осуществлённой до его отзыва."
    )

    # ── Секция 8 ─────────────────────────────────────────────────────────────
    pdf.section_title("8.  Контактные данные Оператора")
    pdf.set_fill_color(255, 248, 220)
    y = pdf.get_y()
    pdf.rect(MARGIN_L, y, TEXT_W, 14, "F")
    pdf.set_xy(MARGIN_L + 4, y + 2)
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.multi_cell(TEXT_W - 8, 5, "[Укажите контактные данные Оператора: e-mail, телефон, адрес]")
    pdf.set_text_color(*COLOR_DARK)
    pdf.ln(6)

    # ── Секция 9 ─────────────────────────────────────────────────────────────
    pdf.section_title("9.  Подтверждение согласия")
    pdf.body_text(
        "Нажимая кнопку «Я согласен» в интерфейсе Сервиса, пользователь подтверждает, что:"
    )
    for item in [
        "ознакомился с настоящим документом в полном объёме;",
        "даёт согласие на обработку персональных данных на указанных условиях;",
        "достиг возраста 18 лет либо действует с согласия законного представителя.",
    ]:
        pdf.bullet(item)

    # ── Дата ─────────────────────────────────────────────────────────────────
    pdf.ln(6)
    pdf.divider()
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.set_x(MARGIN_L)
    pdf.cell(TEXT_W / 2, 6, "Дата вступления в силу: 07.05.2026")
    pdf.cell(TEXT_W / 2, 6, "MedDecode  |  medDecode Bot", align="R")

    pdf.output(output_path)
    print(f"PDF создан: {output_path}")


if __name__ == "__main__":
    generate_consent_pdf()
