from aiogram.utils.keyboard import ReplyKeyboardBuilder



def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Загрузить анализ")
    builder.button(text="Моя подписка")
    return builder.as_markup(resize_keyboard=True)





