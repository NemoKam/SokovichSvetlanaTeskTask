"""Модуль запуска сервера приложения."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import api_router
from database.database import async_engine, init_async_engine
from routes import main_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]: # noqa: ARG001
    """Функция lifespan для FastAPI.

    Args:
        app (FastAPI): Инстанс запускаемомго FastAPI сервера.

    """
    init_async_engine()
    yield
    if async_engine is not None:
        await async_engine.dispose()


app = FastAPI(lifespan=lifespan)


# Подключения метода /api
app.include_router(
    prefix="/api",
    tags=["api"],
    router=api_router,
)

# Подключения базового метода
app.include_router(
    prefix="",
    tags=["main"],
    router=main_router,
)
