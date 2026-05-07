import logging
import uuid

logger = logging.getLogger(__name__)

# Клиент ЮKassa используется для server-side создания платежей (вебхуки).
# Для Telegram Payments достаточно передать provider_token в answer_invoice —
# этот модуль нужен если потребуется прямая интеграция через API ЮKassa.

try:
    from yookassa import Configuration, Payment
    from config import settings

    # YUKASSA_TOKEN используется в Telegram Payments как provider_token
    # Для прямого API ЮKassa нужны YUKASSA_SHOP_ID и YUKASSA_SECRET_KEY
    Configuration.account_id = getattr(settings, "YUKASSA_SHOP_ID", "")
    Configuration.secret_key = getattr(settings, "YUKASSA_SECRET_KEY", "")
    _YOOKASSA_AVAILABLE = True
except Exception:
    _YOOKASSA_AVAILABLE = False
    logger.warning("yookassa не настроена или библиотека не установлена")


def create_payment(amount: float, description: str, return_url: str) -> dict:
    if not _YOOKASSA_AVAILABLE:
        raise RuntimeError("ЮKassa не настроена")

    payment = Payment.create({
        "amount": {"value": str(amount), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": return_url},
        "capture": True,
        "description": description,
    }, uuid.uuid4())

    logger.info("Создан платёж ЮKassa: %s", payment.id)
    return {"payment_id": payment.id, "confirmation_url": payment.confirmation.confirmation_url}
