from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, BigInteger
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base

# Базовый класс для всех моделей — от него наследуются все таблицы
Base = declarative_base()


# Модель таблицы пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # внутренний ID
    telegram_id = Column(BigInteger, unique=True, nullable=False)            # ID пользователя в Telegram
    username = Column(String(100), nullable=True)                            # username (может отсутствовать)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # дата регистрации
    analyses_used = Column(Integer, default=0)                               # счётчик использованных анализов


# Модель таблицы подписок
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # связь с таблицей users
    is_active = Column(Boolean, default=0)                             # активна ли подписка
    expires_at = Column(DateTime, nullable=True)                       # дата окончания подписки
    plan = Column(String(20), default="free")                          # тариф: "free" или "premium"


# Модель таблицы истории анализов
class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # связь с таблицей users
    file_type = Column(String(10), nullable=False)                     # тип файла: "photo" или "pdf"
    result_text = Column(Text, nullable=False)                         # текст расшифровки от OpenAI
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # дата анализа