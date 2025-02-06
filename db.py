import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Загрузим переменные окружения из .env
load_dotenv()

# Считаем параметры подключения к БД
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError("Не заданы все необходимые переменные окружения для подключения к БД!")

# Формируем URL подключения к PostgreSQL с использованием asyncpg
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаём асинхронный движок (engine) для подключения к БД
engine = create_async_engine(DB_URL, echo=True)

# Создаём фабрику асинхронных сессий для взаимодействия с БД
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

# Создаём базовый класс для моделей
Base = declarative_base()
