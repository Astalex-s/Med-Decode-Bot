import logging
import uuid
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.analyze_file import analyze_file
from infrastructure.db.repositories.user_repo import UserRepository
from infrastructure.db.repositories.analysis_repo import AnalysisRepository
from infrastructure.ocr.ocr import OCRService
from infrastructure.pdf.pdf_generator import generate_report_pdf

logger = logging.getLogger(__name__)

analize_router = Router(name=__name__)

EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}
ALLOWED_MIME_TYPES = set(EXTENSIONS.keys())


async def _send_result(message: Message, text: str) -> None:
    """Формирует PDF-отчёт и отправляет его пользователю."""
    try:
        pdf_bytes = generate_report_pdf(text, generated_at=datetime.now())
        filename = f"meddecode_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = BufferedInputFile(pdf_bytes, filename=filename)
        await message.answer_document(
            doc,
            caption="Расшифровка готова. Откройте PDF-файл для просмотра полного отчёта.",
        )
    except Exception:
        logger.exception("Не удалось сгенерировать PDF, отправляю текст")
        # Fallback: отправить текст если PDF не удался
        MAX_MSG_LEN = 4096
        while text:
            chunk = text[:MAX_MSG_LEN]
            text = text[MAX_MSG_LEN:]
            await message.answer(chunk, parse_mode=None)


@analize_router.message(Command("analyze"))
async def analyze_command(message: Message) -> None:
    """Инструкция по загрузке анализа."""
    await message.answer(
        "Отправьте фото или PDF-файл с результатами анализов.\n\n"
        "Бот распознает данные и сформирует подробный отчёт в PDF "
        "с расшифровкой каждого показателя."
    )


@analize_router.message(F.photo)
async def photo_handler(message: Message, session: AsyncSession) -> None:
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    file_path = f"temp/{uuid.uuid4()}.jpg"

    await message.bot.download_file(file.file_path, file_path)
    logger.info("Фото получено от пользователя %d, сохранено в %s", message.from_user.id, file_path)

    status_msg = await message.answer("Фото получено, анализирую...")

    try:
        result = await analyze_file(
            telegram_id=message.from_user.id,
            file_path=file_path,
            file_type="photo",
            user_repo=UserRepository(session),
            analysis_repo=AnalysisRepository(session),
            ocr_service=OCRService(),
        )
        try:
            await status_msg.delete()
        except Exception:
            pass
        await _send_result(message, result)
    except Exception as e:
        logger.exception("Ошибка при обработке фото от пользователя %d", message.from_user.id)
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer("Произошла ошибка при обработке файла. Попробуйте ещё раз.")


@analize_router.message(F.document)
async def document_handler(message: Message, session: AsyncSession) -> None:
    if message.document.mime_type not in ALLOWED_MIME_TYPES:
        await message.answer("Поддерживаются только PDF, PNG и JPEG файлы.")
        return

    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    ext = EXTENSIONS[message.document.mime_type]
    file_path = f"temp/{uuid.uuid4()}{ext}"

    await message.bot.download_file(file.file_path, file_path)
    logger.info("Документ получен от пользователя %d, сохранено в %s", message.from_user.id, file_path)

    file_type = "pdf" if ext == ".pdf" else "photo"
    status_msg = await message.answer("Документ получен, анализирую...")

    try:
        result = await analyze_file(
            telegram_id=message.from_user.id,
            file_path=file_path,
            file_type=file_type,
            user_repo=UserRepository(session),
            analysis_repo=AnalysisRepository(session),
            ocr_service=OCRService(),
        )
        try:
            await status_msg.delete()
        except Exception:
            pass
        await _send_result(message, result)
    except Exception as e:
        logger.exception("Ошибка при обработке документа от пользователя %d", message.from_user.id)
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer("Произошла ошибка при обработке файла. Попробуйте ещё раз.")
