import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from presentation.bot.handlers.consent import consent_router
from presentation.bot.handlers.analyze import analize_router
from presentation.bot.handlers.payment import payment_router
from presentation.bot.handlers.admin import admin_router
from presentation.bot.middlewares.consent_check import ConsentCheckMiddleware
from presentation.bot.middlewares.subscription import SubscriptionMiddleware
from infrastructure.db.session import AsyncSessionLocal
from config import settings

logger = logging.getLogger(__name__)

TOKEN = settings.BOT_TOKEN
dp = Dispatcher(storage=MemoryStorage())


async def db_session_middleware(handler, event, data):
    async with AsyncSessionLocal() as session:
        data["session"] = session
        return await handler(event, data)


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Инъекция сессии БД во все события
    dp.update.outer_middleware(db_session_middleware)

    # Проверка согласия на ПДн (применяется ко всем Message и CallbackQuery)
    dp.message.middleware(ConsentCheckMiddleware())
    dp.callback_query.middleware(ConsentCheckMiddleware())

    # Проверка лимита подписки (только для сообщений с файлами)
    dp.message.middleware(SubscriptionMiddleware())

    # Порядок роутеров важен: consent перехватывает /start первым
    dp.include_router(consent_router)   # /start + согласие ПДн
    dp.include_router(admin_router)     # /export_users
    dp.include_router(payment_router)   # Моя подписка / платежи
    dp.include_router(analize_router)   # фото и документы

    # Меню команд для обычных пользователей
    user_commands = [
        BotCommand(command="analyze", description="Загрузить анализ"),
        BotCommand(command="status", description="Мой статус"),
        BotCommand(command="subscribe", description="Оформить подписку"),
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Расширенное меню для администраторов
    admin_commands = user_commands + [
        BotCommand(command="export", description="Журнал пользователей"),
        BotCommand(command="settings", description="Настройка платежей"),
        BotCommand(command="testpay", description="Тестовый платёж"),
    ]
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception:
            logger.warning("Не удалось установить команды для админа %d", admin_id)

    logger.info("Bot started: @MedDecodeBot")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Bot stopped")


if __name__ == "__main__":
    # Принудительно UTF-8 для Windows-консоли (иначе Unicode-имена ломают логи)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
