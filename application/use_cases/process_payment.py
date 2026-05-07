import logging
from datetime import datetime, timedelta, timezone

from domain.entities.subscription import Subscription
from domain.interfaces.user_repository import IUserRepository

logger = logging.getLogger(__name__)

SUBSCRIPTION_DAYS = 30


async def process_payment(
    telegram_id: int,
    user_repo: IUserRepository,
) -> None:
    """Активирует подписку пользователя после успешной оплаты."""
    user = await user_repo.get_by_telegram_id(telegram_id)
    if user is None:
        logger.error("process_payment: пользователь %d не найден", telegram_id)
        return

    subscription = await user_repo.get_subscription(user.id)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SUBSCRIPTION_DAYS)

    if subscription is None:
        new_sub = Subscription(
            user_id=user.id,
            is_active=True,
            plan="premium",
            expires_at=expires_at,
        )
        await user_repo.create_subscription(new_sub)
        logger.info("Подписка создана для пользователя %d, истекает %s", telegram_id, expires_at)
    else:
        # Продлеваем от текущей даты окончания, если она ещё не истекла
        if subscription.expires_at and subscription.expires_at > datetime.now(timezone.utc):
            expires_at = subscription.expires_at + timedelta(days=SUBSCRIPTION_DAYS)
        subscription.is_active = True
        subscription.plan = "premium"
        subscription.expires_at = expires_at
        await user_repo.update_subscription(subscription)
        logger.info("Подписка продлена для пользователя %d, истекает %s", telegram_id, expires_at)
