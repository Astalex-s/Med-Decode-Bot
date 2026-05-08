import asyncio
import logging
import os

from domain.entities.analysis import Analysis
from domain.interfaces.analysis_repository import IAnalysisRepository
from domain.interfaces.ocr_service import IOCRService
from domain.interfaces.user_repository import IUserRepository
from infrastructure.ai.openai_client import explain_analysis_vision

logger = logging.getLogger(__name__)

# Маркеры нераспознанного документа — только фразы прямого отказа GPT.
# Не использовать общие фразы типа "не удалось" — они встречаются в нормальных отчётах.
_NOT_RECOGNIZED_MARKERS = (
    "не является медицинским анализом",
    "не содержит медицинских данных",
    "не содержит медицинских анализов",
    "не могу распознать",
    "не могу прочитать",
    "изображение нечитаемо",
    "не удалось распознать текст",
    "не удалось прочитать",
)


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

    logger.info("Обработка файла: %s", file_path)
    # Препроцессинг синхронный — запускаем в executor
    loop = asyncio.get_event_loop()
    images_data = await loop.run_in_executor(None, ocr_service.extract_text, file_path)

    if not images_data.strip():
        logger.info("Не удалось обработать изображение — попытка не засчитана для пользователя %d", telegram_id)
        return None  # Сигнал что распознавание не удалось

    # Разделяем страницы (для PDF)
    images_b64 = [img for img in images_data.split("|||PAGE|||") if img.strip()]

    # Отправляем изображения в GPT-4o-mini Vision
    ai_result = await explain_analysis_vision(images_b64)

    # Если GPT сообщил что не может распознать — не засчитываем
    if any(marker in ai_result.lower() for marker in _NOT_RECOGNIZED_MARKERS):
        logger.info("GPT не распознал анализ — попытка не засчитана для пользователя %d", telegram_id)
        return None  # Сигнал что распознавание не удалось

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
