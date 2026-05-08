from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_keyboard(is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.button(text="Загрузить анализ")
    builder.button(text="Моя подписка")
    if is_admin:
        builder.button(text="Панель администратора")
        builder.adjust(2, 1)
    else:
        builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)





