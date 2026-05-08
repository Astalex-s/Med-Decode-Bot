from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def payment_settings_keyboard(free_limit: int, price: int) -> InlineKeyboardMarkup:
    """Inline-клавиатура настроек с текущими значениями."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Бесплатный лимит: {free_limit} анализов",
        callback_data="admin:edit_free_limit",
    )
    builder.button(
        text=f"Цена подписки: {price}",
        callback_data="admin:edit_price",
    )
    builder.adjust(1)
    return builder.as_markup()
