import logging

from aiogram import Router, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.check_subscription import check_subscription
from application.use_cases.process_payment import process_payment
from infrastructure.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

payment_router = Router(name=__name__)

SUBSCRIPTION_PRICE = 29900  # 299 рублей в копейках
CURRENCY = "RUB"


@payment_router.message(F.text == "Моя подписка")
async def subscription_info_handler(message: Message, session: AsyncSession) -> None:
    repo = UserRepository(session)
    allowed, reason = await check_subscription(message.from_user.id, repo)

    user = await repo.get_by_telegram_id(message.from_user.id)
    subscription = await repo.get_subscription(user.id) if user else None

    if subscription and subscription.is_active:
        expires = subscription.expires_at.strftime("%d.%m.%Y") if subscription.expires_at else "бессрочно"
        await message.answer(
            f"Ваша подписка: <b>Premium</b>\n"
            f"Действует до: <b>{expires}</b>\n\n"
            "Неограниченное количество анализов."
        )
    else:
        from config import settings
        used = user.analyses_used if user else 0
        remaining = max(0, settings.FREE_LIMIT - used)
        await message.answer(
            f"Ваша подписка: <b>Бесплатный план</b>\n"
            f"Использовано анализов: <b>{used}/{settings.FREE_LIMIT}</b>\n"
            f"Осталось бесплатных: <b>{remaining}</b>\n\n"
            "Оформите подписку <b>Premium</b> за 299 ₽/мес — неограниченные анализы.\n\n"
            "Нажмите /subscribe для оплаты."
        )


@payment_router.message(F.text == "/subscribe")
async def send_invoice_handler(message: Message) -> None:
    await message.answer_invoice(
        title="Подписка MedDecode Premium",
        description="Неограниченное количество анализов медицинских документов на 30 дней.",
        payload="premium_subscription_30d",
        currency=CURRENCY,
        prices=[LabeledPrice(label="Premium на 30 дней", amount=SUBSCRIPTION_PRICE)],
        provider_token="",  # Для Telegram Stars оставить пустым; для ЮKassa — вставить токен из .env
    )
    logger.info("Инвойс отправлен пользователю %d", message.from_user.id)


@payment_router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery) -> None:
    # Подтверждаем готовность принять платёж
    await query.answer(ok=True)
    logger.info("PreCheckoutQuery подтверждён для пользователя %d", query.from_user.id)


@payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message, session: AsyncSession) -> None:
    logger.info(
        "Успешная оплата от пользователя %d, payload=%s, amount=%d",
        message.from_user.id,
        message.successful_payment.invoice_payload,
        message.successful_payment.total_amount,
    )
    await process_payment(
        telegram_id=message.from_user.id,
        user_repo=UserRepository(session),
    )
    await message.answer(
        "Оплата прошла успешно! Подписка <b>Premium</b> активирована на 30 дней.\n\n"
        "Теперь вы можете загружать неограниченное количество анализов."
    )
