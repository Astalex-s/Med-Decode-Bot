import logging
from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.check_subscription import check_subscription
from infrastructure.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Проверяет лимиты подписки перед обработкой фото и документов.
    Если лимит исчерпан — отправляет сообщение и прерывает обработку.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        # Применяем только к сообщениям с фото или документами
        if not (event.photo or event.document):
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        if session is None:
            return await handler(event, data)

        repo = UserRepository(session)
        allowed, reason = await check_subscription(event.from_user.id, repo)

        if not allowed:
            logger.info(
                "Пользователь %d заблокирован middleware: лимит исчерпан",
                event.from_user.id,
            )
            await event.answer(reason)
            return  # Прерываем цепочку — хендлер не вызывается

        return await handler(event, data)
