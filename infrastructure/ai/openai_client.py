import logging

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты медицинский ассистент, который помогает пациентам понять результаты анализов. "
    "Пользователь отправляет фотографию или скан медицинского документа.\n"
    "Твои задачи:\n"
    "1. Прочитать ВСЕ данные с изображения, включая рукописный текст и печатный.\n"
    "2. Объяснить каждый показатель простым, понятным языком без медицинского жаргона.\n"
    "3. Указать, какие показатели выходят за пределы референсных значений (если они указаны).\n"
    "4. Дать общие рекомендации по образу жизни там, где это уместно.\n"
    "Строгие ограничения:\n"
    "- Никогда не ставь диагнозы.\n"
    "- Всегда рекомендуй обратиться к врачу для интерпретации результатов.\n"
    "- Отвечай на русском языке.\n"
    "- Если изображение нечитаемое или не является медицинским анализом — сообщи об этом."
)


async def explain_analysis_vision(images_b64: list[str]) -> str:
    """Отправляет изображения в GPT-4o-mini Vision и получает расшифровку."""
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    content = [{"type": "text", "text": "Прочитай и расшифруй результаты медицинских анализов на этих изображениях."}]
    for img_b64 in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_b64}",
                "detail": "high",
            },
        })

    logger.info("Отправка %d изображений в OpenAI Vision", len(images_b64))
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.3,
        max_tokens=3000,
    )
    result = response.choices[0].message.content
    logger.info("Получен ответ от OpenAI Vision, длина: %d символов", len(result))
    return result


async def explain_analysis(text: str) -> str:
    """Обратная совместимость: отправляет текст (не изображение) в GPT."""
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    logger.info("Отправка текста в OpenAI, длина: %d символов", len(text))
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    result = response.choices[0].message.content
    logger.info("Получен ответ от OpenAI, длина: %d символов", len(result))
    return result
