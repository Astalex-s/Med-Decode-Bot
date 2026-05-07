import csv
import io
import logging
from datetime import timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from infrastructure.db.models import User, UserConsent, Subscription

logger = logging.getLogger(__name__)

admin_router = Router(name=__name__)


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.ADMIN_IDS


@admin_router.message(Command("export_users"))
async def export_users(message: Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        logger.warning("Попытка вызова /export_users не-администратором: %d", message.from_user.id)
        return

    # Загружаем всех пользователей, их согласия и подписки одним запросом
    users_result = await session.execute(select(User).order_by(User.created_at))
    users = users_result.scalars().all()

    consents_result = await session.execute(select(UserConsent))
    consents = {c.telegram_id: c for c in consents_result.scalars().all()}

    subs_result = await session.execute(select(Subscription))
    subs = {s.user_id: s for s in subs_result.scalars().all()}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL)

    writer.writerow([
        "ID", "Telegram ID", "Username", "Полное имя",
        "Дата регистрации", "Анализов использовано",
        "Согласие ПДн", "Дата согласия",
        "Подписка", "Тариф", "Подписка до",
    ])

    for user in users:
        consent = consents.get(user.telegram_id)
        sub = subs.get(user.id)

        agreed = "Да" if (consent and consent.agreed) else "Нет"
        agreed_at = ""
        if consent and consent.agreed_at:
            agreed_at = consent.agreed_at.strftime("%d.%m.%Y %H:%M")

        sub_active = ""
        sub_plan = ""
        sub_expires = ""
        if sub:
            sub_active = "Активна" if sub.is_active else "Неактивна"
            sub_plan = sub.plan or ""
            if sub.expires_at:
                sub_expires = sub.expires_at.strftime("%d.%m.%Y")

        full_name = (consent.full_name or "") if consent else ""
        reg_date = user.created_at.strftime("%d.%m.%Y %H:%M") if user.created_at else ""

        writer.writerow([
            user.id,
            user.telegram_id,
            user.username or "",
            full_name,
            reg_date,
            user.analyses_used,
            agreed,
            agreed_at,
            sub_active,
            sub_plan,
            sub_expires,
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")  # utf-8-sig — корректно открывается в Excel
    file = BufferedInputFile(csv_bytes, filename="meddecode_users.csv")

    await message.answer_document(file, caption=f"Экспорт пользователей: {len(users)} записей.")
    logger.info("Администратор %d выгрузил список пользователей (%d записей)", message.from_user.id, len(users))
