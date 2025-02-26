from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER


if not all([DB_USER, DB_PASS, DB_NAME]):
    raise ValueError("Не заданы все необходимые переменные окружения для подключения к БД!")

# Формируем URL подключения к PostgreSQL с использованием asyncpg
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаём асинхронный движок (engine) для подключения к БД
engine = create_async_engine(DB_URL, echo=False)

# Создаём фабрику асинхронных сессий для взаимодействия с БД
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

# Создаём базовый класс для моделей
Base = declarative_base()
