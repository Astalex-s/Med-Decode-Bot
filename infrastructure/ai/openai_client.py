import logging

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты медицинский ассистент, который помогает пациентам понять результаты анализов. "
    "Твои задачи:\n"
    "1. Объяснить каждый показатель простым, понятным языком без медицинского жаргона.\n"
    "2. Указать, какие показатели выходят за пределы референсных значений (если они указаны).\n"
    "3. Дать общие рекомендации по образу жизни там, где это уместно.\n"
    "Строгие ограничения:\n"
    "- Никогда не ставь диагнозы.\n"
    "- Всегда рекомендуй обратиться к врачу для интерпретации результатов.\n"
    "- Отвечай на русском языке.\n"
    "- Если текст нечитаемый или не является медицинским анализом — сообщи об этом."
)


async def explain_analysis(text: str) -> str:
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
