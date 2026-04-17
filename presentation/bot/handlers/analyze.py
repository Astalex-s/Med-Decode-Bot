from aiogram import Router, F
from aiogram.types import Message

import uuid 

analize_router = Router(name=__name__)

    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
@analize_router.message(F.photo)
async def photo_handler(message: Message) -> None:
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    await message.bot.download_file(file_path, f"temp/{uuid.uuid4()}.jpg")
    await message.answer("Фото получено, обрабатываем...")

@analize_router.message(F.document)
async def document_handler(message: Message) -> None:
    if message.document.mime_type != "application/pdf":
        await message.answer("Только PDF-файлы")
        return
    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    extensions = {
      "application/pdf": ".pdf",
      "image/png": ".png",
      "image/jpeg": ".jpg"
  }
    ext = extensions[message.document.mime_type]
    await message.bot.download_file(file_path, f"temp/{uuid.uuid4()}{ext}")
    await message.answer("Документ получен, обрабатываем...")
