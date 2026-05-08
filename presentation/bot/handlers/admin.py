import csv
import io
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from infrastructure.db.models import User, UserConsent, Subscription
from infrastructure.db.repositories.config_repo import ConfigRepository
from infrastructure.db.repositories.user_repo import UserRepository
from application.use_cases.process_payment import process_payment
from presentation.bot.keyboards.admin_kb import admin_keyboard, payment_settings_keyboard
from presentation.bot.keyboards.main_kb import main_keyboard

logger = logging.getLogger(__name__)

admin_router = Router(name=__name__)

# Ключи настроек в БД
KEY_FREE_LIMIT = "free_limit"
KEY_SUBSCRIPTION_PRICE = "subscription_price"


class AdminSettings(StatesGroup):
    waiting_free_limit = State()
    waiting_price = State()


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.ADMIN_IDS


# ─── Вход / выход из панели ──────────────────────────────────────────────────

@admin_router.message(F.text == "Панель администратора")
async def enter_admin_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "Панель администратора",
        reply_markup=admin_keyboard(),
    )


@admin_router.message(F.text == "Назад")
async def exit_admin_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "Главное меню",
        reply_markup=main_keyboard(is_admin=True),
    )


# ─── Журнал пользователей ────────────────────────────────────────────────────

@admin_router.message(F.text == "Журнал пользователей")
@admin_router.message(Command("export_users"))
async def export_users(message: Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        logger.warning("Попытка выгрузки журнала не-администратором: %d", message.from_user.id)
        return

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
        agreed_at = consent.agreed_at.strftime("%d.%m.%Y %H:%M") if (consent and consent.agreed_at) else ""

        sub_active = sub_plan = sub_expires = ""
        if sub:
            sub_active = "Активна" if sub.is_active else "Неактивна"
            sub_plan = sub.plan or ""
            if sub.expires_at:
                sub_expires = sub.expires_at.strftime("%d.%m.%Y")

        full_name = (consent.full_name or "") if consent else ""
        reg_date = user.created_at.strftime("%d.%m.%Y %H:%M") if user.created_at else ""

        writer.writerow([
            user.id, user.telegram_id, user.username or "", full_name,
            reg_date, user.analyses_used,
            agreed, agreed_at,
            sub_active, sub_plan, sub_expires,
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    file = BufferedInputFile(csv_bytes, filename="meddecode_users.csv")
    await message.answer_document(file, caption=f"Журнал пользователей: {len(users)} записей.")
    logger.info("Администратор %d выгрузил журнал пользователей (%d записей)", message.from_user.id, len(users))


# ─── Тестовый платёж ─────────────────────────────────────────────────────────

@admin_router.message(F.text == "Тестовый платёж")
@admin_router.message(Command("test_pay"))
async def test_pay_handler(message: Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    await process_payment(
        telegram_id=message.from_user.id,
        user_repo=UserRepository(session),
    )
    logger.info("Тестовая активация Premium для администратора %d", message.from_user.id)
    await message.answer(
        "[ТЕСТ] Подписка <b>Premium</b> активирована на 30 дней.\n\n"
        "Неограниченное количество анализов доступно."
    )


# ─── Настройка платежей ───────────────────────────────────────────────────────

async def _get_current_settings(session: AsyncSession) -> tuple[int, int]:
    config = ConfigRepository(session)
    free_limit = int(await config.get(KEY_FREE_LIMIT, str(settings.FREE_LIMIT)))
    price = int(await config.get(KEY_SUBSCRIPTION_PRICE, "300"))
    return free_limit, price


@admin_router.message(F.text == "Настройка платежей")
async def show_payment_settings(message: Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    free_limit, price = await _get_current_settings(session)
    await message.answer(
        "<b>Настройка платежей</b>\n\n"
        f"Бесплатный лимит: <b>{free_limit}</b> анализов\n"
        f"Цена подписки: <b>{price} ⭐</b> / мес\n\n"
        "Нажмите кнопку для изменения параметра:",
        reply_markup=payment_settings_keyboard(free_limit, price),
    )


@admin_router.callback_query(F.data == "admin:edit_free_limit")
async def ask_free_limit(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer(
        "Введите новое количество бесплатных анализов (целое число, например <b>3</b>):"
    )
    await state.set_state(AdminSettings.waiting_free_limit)


@admin_router.callback_query(F.data == "admin:edit_price")
async def ask_price(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer(
        "Введите новую цену подписки в Telegram Stars (целое число, например <b>300</b>):"
    )
    await state.set_state(AdminSettings.waiting_price)


@admin_router.message(AdminSettings.waiting_free_limit)
async def save_free_limit(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Введите целое число, например: <b>3</b>")
        return
    value = int(message.text.strip())
    if value < 0:
        await message.answer("Значение не может быть отрицательным.")
        return

    config = ConfigRepository(session)
    await config.set(KEY_FREE_LIMIT, str(value))
    await state.clear()

    _, price = await _get_current_settings(session)
    logger.info("Администратор %d изменил бесплатный лимит на %d", message.from_user.id, value)
    await message.answer(
        f"Бесплатный лимит обновлён: <b>{value}</b> анализов",
        reply_markup=payment_settings_keyboard(value, price),
    )


@admin_router.message(AdminSettings.waiting_price)
async def save_price(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Введите целое число, например: <b>300</b>")
        return
    value = int(message.text.strip())
    if value < 1:
        await message.answer("Цена должна быть не менее 1.")
        return

    config = ConfigRepository(session)
    await config.set(KEY_SUBSCRIPTION_PRICE, str(value))
    await state.clear()

    free_limit, _ = await _get_current_settings(session)
    logger.info("Администратор %d изменил цену подписки на %d stars", message.from_user.id, value)
    await message.answer(
        f"Цена подписки обновлена: <b>{value} ⭐</b> / мес",
        reply_markup=payment_settings_keyboard(free_limit, value),
    )
