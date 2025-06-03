"""Модуль настройки подключения к базе данных."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import DATABASE_ASYNC_URL

async_engine: AsyncEngine | None = None
async_session_local: async_sessionmaker[AsyncSession] | None = None

def init_async_engine() -> None:
    """Функция инициализации базы данных."""
    global async_engine, async_session_local
    async_engine = create_async_engine(DATABASE_ASYNC_URL)
    async_session_local = async_sessionmaker(async_engine)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Получение Ассинхронного генератора сессии подключения к БД (Для Depends).

    Returns:
        AsyncGenerator[AsyncSession]: Ассинхронный генератор сессии подключения к БД.

    Yields:
        Iterator[AsyncGenerator[AsyncSession]]: Сессия подключения к БД.

    """
    if async_session_local is not None:
        db = async_session_local()
        try:
            yield db
        finally:
            await db.close()
