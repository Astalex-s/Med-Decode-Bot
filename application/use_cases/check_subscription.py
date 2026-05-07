import logging
from datetime import datetime, timezone

from config import settings
from domain.entities.subscription import Subscription
from domain.interfaces.user_repository import IUserRepository

logger = logging.getLogger(__name__)


async def check_subscription(
    telegram_id: int,
    user_repo: IUserRepository,
) -> tuple[bool, str]:
    """
    Проверяет, может ли пользователь выполнить анализ.

    Возвращает (allowed: bool, reason: str).
    reason — пустая строка если разрешено, иначе текст сообщения пользователю.
    """
    user = await user_repo.get_by_telegram_id(telegram_id)
    if user is None:
        return False, "Пользователь не найден. Введите /start для регистрации."

    subscription = await user_repo.get_subscription(user.id)

    # Если подписка есть — проверяем срок действия
    if subscription and subscription.is_active:
        expires = subscription.expires_at
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires and expires < datetime.now(timezone.utc):
            # Подписка истекла — деактивируем
            subscription.is_active = False
            await user_repo.update_subscription(subscription)
            logger.info("Подписка пользователя %d истекла, деактивирована", telegram_id)
        else:
            return True, ""

    # Нет активной подписки — проверяем бесплатный лимит
    if user.analyses_used < settings.FREE_LIMIT:
        remaining = settings.FREE_LIMIT - user.analyses_used
        logger.info("Пользователь %d: использовано %d/%d анализов", telegram_id, user.analyses_used, settings.FREE_LIMIT)
        return True, ""

    return False, (
        f"Вы использовали все {settings.FREE_LIMIT} бесплатных анализа.\n\n"
        "Оформите подписку для продолжения — нажмите кнопку «Моя подписка»."
    )
