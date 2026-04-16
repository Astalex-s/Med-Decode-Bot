from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    BOT_TOKEN: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    OPENAI_API_KEY: str
    YOOMONEY_TOKEN: str
    FREE_LIMIT: int

settings = Settings()
