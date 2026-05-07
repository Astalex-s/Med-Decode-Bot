import logging
from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.repositories.consent_repo import ConsentRepository
from presentation.bot.handlers.consent import consent_keyboard, CONSENT_TEXT

logger = logging.getLogger(__name__)

# callback_data и команды, которые НЕ блокируем (до согласия)
_CONSENT_CALLBACKS = {"consent:agree", "consent:decline", "consent:document"}
_ALLOWED_COMMANDS = {"/start", "/test_pay"}


class ConsentCheckMiddleware(BaseMiddleware):
    """
    Проверяет, что пользователь дал согласие на обработку ПДн.
    Если нет — показывает экран согласия и прерывает обработку.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Определяем telegram_id и тип события
        if isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id
            # Не блокируем сами callback'и согласия
            if event.data in _CONSENT_CALLBACKS:
                return await handler(event, data)
        elif isinstance(event, Message):
            telegram_id = event.from_user.id
            # Не блокируем /start — там своя логика
            if event.text and event.text.strip().split()[0] in _ALLOWED_COMMANDS:
                return await handler(event, data)
        else:
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        if session is None:
            return await handler(event, data)

        repo = ConsentRepository(session)
        consent = await repo.get_by_telegram_id(telegram_id)

        if consent and consent.agreed:
            return await handler(event, data)

        # Согласие не дано — показываем экран согласия
        logger.info("Пользователь %d не дал согласие на ПДн — заблокирован", telegram_id)
        if isinstance(event, Message):
            await event.answer(CONSENT_TEXT, reply_markup=consent_keyboard())
        elif isinstance(event, CallbackQuery):
            await event.answer("Необходимо дать согласие на обработку данных.", show_alert=True)
            await event.message.answer(CONSENT_TEXT, reply_markup=consent_keyboard())
