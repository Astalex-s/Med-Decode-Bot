from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, BigInteger, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyses_used = Column(Integer, default=0)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    plan = Column(String(20), default="free")


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String(10), nullable=False)
    result_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BotConfig(Base):
    """Динамические настройки бота, изменяемые через панель администратора."""
    __tablename__ = "bot_config"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)


class UserConsent(Base):
    """Журнал согласий на обработку персональных данных (ФЗ-152 РФ)."""
    __tablename__ = "user_consents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)       # имя из Telegram-профиля
    username = Column(String(100), nullable=True)        # @username
    agreed = Column(Boolean, nullable=False, default=False)
    agreed_at = Column(DateTime(timezone=True), nullable=True)
    declined_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
