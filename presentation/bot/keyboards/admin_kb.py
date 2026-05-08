from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def admin_keyboard():
    """Клавиатура панели администратора."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="Журнал пользователей")
    builder.button(text="Тестовый платёж")
    builder.button(text="Настройка платежей")
    builder.button(text="Назад")
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def payment_settings_keyboard(free_limit: int, price: int) -> InlineKeyboardMarkup:
    """Inline-клавиатура настроек с текущими значениями."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Бесплатный лимит: {free_limit} анализов",
        callback_data="admin:edit_free_limit",
    )
    builder.button(
        text=f"Цена подписки: {price} ⭐",
        callback_data="admin:edit_price",
    )
    builder.adjust(1)
    return builder.as_markup()
