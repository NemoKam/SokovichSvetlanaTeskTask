"""Файл конфигурации тестов."""
from collections.abc import AsyncGenerator

import pytest_asyncio
from _pytest.fixtures import SubRequest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import DATABASE_URL_SUFFIX, TEST_DATABASE_NAME
from core.services import get_urls_service
from database.database import get_db
from database.models import Base, ShortedUrl
from fast import app


# ----------------------------------------------------------------------
# Конфигурация тестовой базы данных для FAST API сервера
@pytest_asyncio.fixture(scope="session", autouse=True)
async def async_engine() -> AsyncGenerator[AsyncEngine]:
    """Фикстура для создания async_engine'а."""
    yield create_async_engine("postgresql+asyncpg" + \
                                DATABASE_URL_SUFFIX.format(TEST_DATABASE_NAME), \
                                echo=False, future=True)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def async_session_local(
    async_engine: AsyncEngine
) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    """Фикстура для создания async_sessionmaker'а."""
    yield async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database(async_engine: AsyncEngine) -> AsyncGenerator[None]:
    """Фикстура для setup'а тестовой базы данных."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Функциия для получения асинхронной сессии к тестовой базе данных
@pytest_asyncio.fixture(scope="session", autouse=True)
async def override_get_db(
    async_session_local: async_sessionmaker[AsyncSession]
) -> None:
    """Фикстура для оверрайдинга текущей функции get_db в целях тестирования."""
    # Причина вложенности кроется в ошибке, возникающей из-за аннотации.
    # Нельзя овверайдить функцию с переданным аргументов,
    # аннотация которого = async_sessionmaker[AsyncSession]
    # Так как async_sessionmaker[AsyncSession] is not a valid Pydantic Field
    async def _get_test_db() -> AsyncGenerator[AsyncSession]:
        async with async_session_local() as db:
            yield db
    app.dependency_overrides[get_db] = _get_test_db

# ----------------------------------------------------------------------


# Фикстура для подключения к базе данных
@pytest_asyncio.fixture(scope="session")
async def connection(async_engine: AsyncEngine) -> AsyncGenerator[AsyncConnection]:
    """Фикстура для создания асинхронного подключения к базе данных."""
    async with async_engine.connect() as connection:
        yield connection

@pytest_asyncio.fixture(scope="session")
async def session(
    connection: AsyncConnection
) -> AsyncGenerator[AsyncSession]:
    """Фикстура для создания асинхронной сессии базы данных."""
    async_session = AsyncSession(bind=connection)
    try:
        yield async_session
    finally:
        await async_session.close()
        await connection.close()


# Фикстура пустого клиента для тестов
@pytest_asyncio.fixture(scope="session")
async def base_client() -> AsyncGenerator[AsyncClient]:
    """Возвращает AsyncClient модель."""
    async with LifespanManager(app), AsyncClient(transport=ASGITransport(app=app),
                        base_url="http://127.0.0.1:8000",
                        headers={"Content-Type": "application/json"}) as client:
            yield client


@pytest_asyncio.fixture(scope="session")
async def unauthorized_client(base_client: AsyncClient) -> AsyncGenerator[AsyncClient]:
    """Возвращает AsyncClient, подключённый к приложению FastAPI."""
    yield base_client


# Фикстура с тестовыми ссылками для получения
@pytest_asyncio.fixture(scope="session", params=["ABBA", None])
async def existing_shorted_url(
    request: SubRequest,
    session: AsyncSession
) -> ShortedUrl:
    """Возвращает тестовый ShortedUrl."""
    return await get_urls_service(session) \
        .create_new_url_with_lock("https://www.wikipedia.ru/", request.param)


# Фикстура с тестовыми ссылками для удаления
@pytest_asyncio.fixture(scope="session", params=["DEL_AA", None, "DEL_BB"])
async def existing_shorted_url_for_deleting(
    request: SubRequest,
    session: AsyncSession
) -> ShortedUrl:
    """Возвращает тестовый ShortedUrl для удаления."""
    return await get_urls_service(session) \
        .create_new_url_with_lock("https://delete.me/", request.param)



# Фикстура с тестовыми ссылками
@pytest_asyncio.fixture(scope="session")
async def existing_shorted_url_for_get_links(
    session: AsyncSession
) -> list[ShortedUrl]:
    """Возвращает список тестовых ShortedUrl для получения списка ссылок."""
    return [await get_urls_service(session). \
                create_new_url_with_lock("https://www.test_list.ru/", None)
                for _ in range(100)]
