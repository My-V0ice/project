# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Читаем параметры БД из переменных окружения
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "postgres")

# Формируем строку подключения
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Создаём асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # True для отладки SQL-запросов
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,   # Переподключение через час
)

# Сессия для работы с БД
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Зависимость для получения сессии в роутах
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Функция для создания таблиц (для разработки)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)