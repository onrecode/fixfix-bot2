"""
Подключение к базе данных PostgreSQL
"""
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings

# Создаем асинхронный движок
engine = create_async_engine(
    settings.database.url,
    echo=settings.api.debug,
    poolclass=NullPool if settings.api.debug else None,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных"""
    from app.database.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Закрытие соединений с базой данных"""
    await engine.dispose()


# Функция для проверки подключения
async def check_db_connection() -> bool:
    """Проверка подключения к базе данных"""
    try:
        print(f"DEBUG: Проверка подключения к БД: {settings.database.url}")
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print(f"DEBUG: Результат запроса: {result}")
        print("DEBUG: Подключение к БД успешно!")
        return True
    except Exception as e:
        print(f"DEBUG: Ошибка подключения к БД: {e}")
        print(f"DEBUG: Тип ошибки: {type(e)}")
        return False
