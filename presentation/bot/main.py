import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импортируем роутеры из обработчиков — каждый роутер отвечает за свою группу команд
from presentation.bot.handlers.start import my_router
from presentation.bot.handlers.analyze import analize_router
# Импортируем настройки из config.py — там хранятся все переменные из .env
from config import settings

# Токен бота берём из настроек (не хардкодим прямо в коде)
TOKEN = settings.BOT_TOKEN

# Dispatcher — главный объект aiogram, принимает все обновления от Telegram
dp = Dispatcher()


async def main() -> None:
    # Создаём объект бота с токеном и настройкой HTML-разметки по умолчанию
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Подключаем роутеры к диспетчеру — порядок важен, обработчики проверяются сверху вниз
    dp.include_router(my_router)      # обработчики команды /start
    dp.include_router(analize_router) # обработчики фото и документов

    try:
        # Запускаем long polling — бот начинает слушать сообщения от Telegram
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        # Игнорируем ошибку при принудительной остановке (Ctrl+C)
        pass


if __name__ == "__main__":
    # Настройка логирования: выводим INFO-сообщения в консоль
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Подавляем ошибку KeyboardInterrupt на уровне asyncio
        pass