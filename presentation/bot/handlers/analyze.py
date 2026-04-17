from aiogram import Router, F
from aiogram.types import Message
import uuid

# Роутер для обработчиков приёма файлов (фото и документы)
analize_router = Router(name=__name__)

# Словарь соответствия MIME-типов и расширений файлов
EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg"
}

# Допустимые MIME-типы для документов
ALLOWED_MIME_TYPES = set(EXTENSIONS.keys())


# Обработчик фотографий — срабатывает когда пользователь отправляет фото
@analize_router.message(F.photo)
async def photo_handler(message: Message) -> None:
    # Берём последнее фото в списке — оно всегда наилучшего качества
    file_id = message.photo[-1].file_id

    # Получаем информацию о файле с серверов Telegram
    file = await message.bot.get_file(file_id)
    file_path = file.file_path

    # Скачиваем файл в папку temp/ с уникальным именем через uuid
    await message.bot.download_file(file_path, f"temp/{uuid.uuid4()}.jpg")
    await message.answer("Фото получено, обрабатываем...")


# Обработчик документов — срабатывает когда пользователь отправляет файл
@analize_router.message(F.document)
async def document_handler(message: Message) -> None:
    # Проверяем что файл нужного типа (PDF, PNG или JPEG)
    if message.document.mime_type not in ALLOWED_MIME_TYPES:
        await message.answer("Поддерживаются только PDF, PNG и JPEG файлы")
        return

    file_id = message.document.file_id

    # Получаем информацию о файле с серверов Telegram
    file = await message.bot.get_file(file_id)
    file_path = file.file_path

    # Определяем расширение файла по его MIME-типу
    ext = EXTENSIONS[message.document.mime_type]

    # Скачиваем файл в папку temp/ с уникальным именем через uuid
    await message.bot.download_file(file_path, f"temp/{uuid.uuid4()}{ext}")
    await message.answer("Документ получен, обрабатываем...")
