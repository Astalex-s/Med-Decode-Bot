from pydantic_settings import BaseSettings, SettingsConfigDict


# Класс настроек — автоматически загружает переменные из файла .env
class Settings(BaseSettings):
    # Указываем путь к .env файлу и кодировку
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str       # токен Telegram-бота от BotFather
    DB_HOST: str         # хост базы данных PostgreSQL
    DB_PORT: int         # порт базы данных (обычно 5432)
    DB_NAME: str         # название базы данных
    DB_USER: str         # пользователь базы данных
    DB_PASSWORD: str     # пароль базы данных
    DB_URL: str          # полная строка подключения к БД (для SQLAlchemy)
    REDIS_HOST: str      # хост Redis (используется для кэширования/очередей)
    REDIS_PORT: int      # порт Redis (обычно 6379)
    OPENAI_API_KEY: str  # ключ API OpenAI для расшифровки анализов
    YOOMONEY_TOKEN: str  # токен ЮMoney для платежей
    FREE_LIMIT: int      # количество бесплатных анализов для пользователя


# Глобальный объект настроек — импортируется во всех модулях проекта
settings = Settings()
