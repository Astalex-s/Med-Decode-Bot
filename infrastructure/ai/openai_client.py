import logging

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты опытный врач клинической лабораторной диагностики с 20-летним стажем. "
    "Пользователь отправляет фотографию или скан медицинского документа.\n\n"
    "ПОРЯДОК ОТВЕТА:\n\n"
    "1. СЧИТАННЫЕ ДАННЫЕ\n"
    "Прочитай ВСЕ данные с изображения (печатный и рукописный текст). "
    "Перечисли каждый показатель с его значением и единицами измерения в виде таблицы.\n\n"
    "2. ПОДРОБНЫЙ РАЗБОР КАЖДОГО ПОКАЗАТЕЛЯ\n"
    "Для каждого показателя укажи:\n"
    "- Название полное и сокращённое\n"
    "- Полученное значение и референсный диапазон (норма)\n"
    "- Статус: НОРМА / ВЫШЕ НОРМЫ / НИЖЕ НОРМЫ\n"
    "- Что означает этот показатель и за что отвечает в организме\n"
    "- Если отклонение — подробно объясни возможные причины (перечисли 3-5 причин), "
    "какие состояния и заболевания могут приводить к такому изменению\n"
    "- Какие дополнительные обследования могут потребоваться при отклонении\n\n"
    "3. ОБЩАЯ ОЦЕНКА\n"
    "Сделай общее заключение по всем результатам в совокупности. "
    "Укажи, какие показатели вызывают наибольшее внимание и почему. "
    "Отметь связи между показателями если они есть.\n\n"
    "4. РЕКОМЕНДАЦИИ\n"
    "Дай конкретные рекомендации по питанию, образу жизни, дополнительным обследованиям.\n\n"
    "5. ДИСКЛЕЙМЕР\n"
    "В конце ОБЯЗАТЕЛЬНО напиши:\n"
    "«Данная расшифровка носит информационно-рекомендательный характер и не является "
    "медицинским диагнозом. Для постановки диагноза и назначения лечения обратитесь "
    "к лечащему врачу.»\n\n"
    "ПРАВИЛА:\n"
    "- Отвечай развёрнуто и подробно, как если бы объяснял пациенту на приёме\n"
    "- Используй понятный язык, но не упрощай медицинскую суть\n"
    "- Отвечай на русском языке\n"
    "- Если изображение нечитаемое или не является медицинским анализом — сообщи об этом"
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
        max_tokens=4096,
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
