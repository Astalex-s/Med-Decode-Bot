import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

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
dp = Dispatcher()


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

    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Бот остановлен")


if __name__ == "__main__":
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
