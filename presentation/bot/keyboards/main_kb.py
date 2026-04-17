from aiogram.utils.keyboard import ReplyKeyboardBuilder


# Функция создаёт и возвращает главную Reply-клавиатуру с двумя кнопками
def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Загрузить анализ")  # кнопка для отправки файла на анализ
    builder.button(text="Моя подписка")      # кнопка для просмотра статуса подписки
    # resize_keyboard=True — уменьшает кнопки до компактного размера
    return builder.as_markup(resize_keyboard=True)





