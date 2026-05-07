import asyncio
import logging
import os

from domain.entities.analysis import Analysis
from domain.interfaces.analysis_repository import IAnalysisRepository
from domain.interfaces.ocr_service import IOCRService
from domain.interfaces.user_repository import IUserRepository
from infrastructure.ai.openai_client import explain_analysis
from infrastructure.ocr.text_processor import process_ocr_text

logger = logging.getLogger(__name__)


async def analyze_file(
    telegram_id: int,
    file_path: str,
    file_type: str,
    user_repo: IUserRepository,
    analysis_repo: IAnalysisRepository,
    ocr_service: IOCRService,
) -> str:
    user = await user_repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise ValueError(f"Пользователь с telegram_id={telegram_id} не найден")

    logger.info("Запуск OCR для файла: %s", file_path)
    # OCR синхронный — запускаем в executor, чтобы не блокировать event loop
    loop = asyncio.get_event_loop()
    raw_text = await loop.run_in_executor(None, ocr_service.extract_text, file_path)
    logger.info("OCR завершён, извлечено символов: %d", len(raw_text))

    structured_text = process_ocr_text(raw_text)

    if not structured_text.strip():
        logger.info("OCR не извлёк текст — попытка не засчитана для пользователя %d", telegram_id)
        return "Не удалось распознать текст на изображении. Попробуйте загрузить более чёткое фото.\n\nПопытка не засчитана."

    ai_result = await explain_analysis(structured_text)

    # Если GPT сообщил что текст нечитаем или не является анализом — не засчитываем
    _not_recognized_markers = (
        "не является медицинским",
        "нечитаемый",
        "не удалось",
        "не могу распознать",
        "не содержит медицинских",
    )
    if any(marker in ai_result.lower() for marker in _not_recognized_markers):
        logger.info("GPT не распознал анализ — попытка не засчитана для пользователя %d", telegram_id)
        return ai_result + "\n\n<i>Попытка не засчитана.</i>"

    analysis = Analysis(
        user_id=user.id,
        file_type=file_type,
        result_text=ai_result,
    )
    await analysis_repo.save(analysis)
    await user_repo.increment_analyses_used(telegram_id)

    # Удаляем временный файл
    try:
        os.remove(file_path)
    except OSError:
        logger.warning("Не удалось удалить временный файл: %s", file_path)

    return ai_result
