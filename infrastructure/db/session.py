from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import settings

# Строка подключения к базе данных берётся из настроек
url = settings.DB_URL

# Асинхронный движок SQLAlchemy — управляет соединением с PostgreSQL
# echo=True означает что все SQL-запросы будут выводиться в консоль (удобно при разработке)
engine = create_async_engine(url, echo=True)

# Фабрика сессий — используется для создания сессий работы с БД
# expire_on_commit=False — объекты не сбрасываются после коммита (важно для async)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

