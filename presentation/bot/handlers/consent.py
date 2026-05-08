import logging
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile,
)
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.consent import UserConsent
from domain.entities.user import User
from infrastructure.db.repositories.consent_repo import ConsentRepository
from infrastructure.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

consent_router = Router(name=__name__)

CONSENT_TEXT = (
    "<b>Согласие на обработку персональных данных</b>\n\n"
    "В соответствии с ФЗ-152 «О персональных данных» Сервис MedDecode обрабатывает:\n"
    "• Ваш Telegram ID, имя и @username\n"
    "• Загружаемые медицинские документы (для распознавания текста)\n\n"
    "Данные используются исключительно для работы Сервиса. "
    "Текст анализов передаётся в OpenAI в обезличенном виде.\n\n"
    "Вы можете ознакомиться с полным текстом документа по кнопке ниже.\n\n"
    "<b>Для использования бота необходимо дать согласие.</b>"
)


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Полный текст документа", callback_data="consent:document")],
        [
            InlineKeyboardButton(text="✅ Я согласен", callback_data="consent:agree"),
            InlineKeyboardButton(text="❌ Отказываюсь", callback_data="consent:decline"),
        ],
    ])


@consent_router.message(CommandStart())
async def start_with_consent(message: Message, session: AsyncSession) -> None:
    repo = ConsentRepository(session)
    consent = await repo.get_by_telegram_id(message.from_user.id)

    if consent and consent.agreed:
        # Уже согласился — регистрируем если нужно и показываем меню
        await _register_and_greet(message, session)
        return

    await message.answer(CONSENT_TEXT, reply_markup=consent_keyboard())


async def _safe_answer(callback: CallbackQuery, text: str = "", show_alert: bool = False) -> None:
    """Отвечает на callback, игнорируя ошибку устаревшего запроса."""
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest:
        pass


@consent_router.callback_query(F.data == "consent:document")
async def send_consent_document(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    doc = FSInputFile("consent_document.pdf", filename="Согласие_на_обработку_ПДн_MedDecode.pdf")
    await callback.message.answer_document(
        doc,
        caption="Полный текст согласия на обработку персональных данных."
    )


@consent_router.callback_query(F.data == "consent:agree")
async def handle_agree(callback: CallbackQuery, session: AsyncSession) -> None:
    await _safe_answer(callback, "Согласие зафиксировано.")

    repo = ConsentRepository(session)
    consent = UserConsent(
        telegram_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
        agreed=True,
        agreed_at=datetime.now(timezone.utc),
    )
    await repo.save(consent)
    logger.info("Пользователь %d (@%s) дал согласие на обработку ПДн", callback.from_user.id, callback.from_user.username)

    # Удаляем сообщение с согласием
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        # Если не удалось удалить — просто убираем кнопки
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

    # Регистрируем в users и отправляем инструкцию
    await _register_and_greet(callback.message, session, callback.from_user)


@consent_router.callback_query(F.data == "consent:decline")
async def handle_decline(callback: CallbackQuery, session: AsyncSession) -> None:
    await _safe_answer(callback, "Вы отказались от обработки данных.", show_alert=True)

    repo = ConsentRepository(session)
    consent = UserConsent(
        telegram_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
        agreed=False,
        declined_at=datetime.now(timezone.utc),
    )
    await repo.save(consent)
    logger.info("Пользователь %d отказался от обработки ПДн", callback.from_user.id)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Вы отказались от обработки персональных данных.\n\n"
        "К сожалению, без согласия использование бота невозможно.\n"
        "Если передумаете — введите /start."
    )


WELCOME_TEXT = (
    "<b>Как пользоваться ботом:</b>\n\n"
    "1. Отправьте фото или PDF с результатами анализов — бот "
    "распознает данные и сформирует подробный отчёт в PDF.\n"
    "2. Отчёт включает расшифровку каждого показателя, "
    "общую оценку и рекомендации.\n"
    "3. Вы можете отправить несколько страниц одного анализа — "
    "просто прикрепите все фото.\n\n"
    "<b>Команды:</b>\n"
    "/analyze — загрузить анализ\n"
    "/status — мой статус и подписка\n"
    "/subscribe — оформить подписку Premium\n\n"
    "Нажмите кнопку <b>Меню</b> слева от поля ввода, "
    "чтобы увидеть все доступные команды."
)


async def _register_and_greet(message: Message, session: AsyncSession, user_obj=None) -> None:
    """Регистрирует пользователя в БД (если ещё нет) и отправляет инструкцию."""
    from_user = user_obj or message.from_user
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(from_user.id)

    if user is None:
        new_user = User(
            telegram_id=from_user.id,
            username=from_user.username,
        )
        await user_repo.create(new_user)
        logger.info("Зарегистрирован пользователь %d (@%s)", from_user.id, from_user.username)

    # Отправляем фото с инструкцией
    photo = FSInputFile("assets/welcome.jpg")
    instruction_msg = await message.answer_photo(
        photo,
        caption=f"<b>{from_user.full_name}</b>, добро пожаловать в MedDecode!\n\n"
        + WELCOME_TEXT,
    )

    # Закрепляем сообщение с инструкцией
    try:
        await instruction_msg.pin(disable_notification=True)
    except TelegramBadRequest:
        logger.warning("Не удалось закрепить сообщение для пользователя %d", from_user.id)
