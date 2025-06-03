"""Модуль метода /api ."""
from fastapi import APIRouter

from api.links.routes import links_router
from api.shorten.routes import shorten_router

api_router = APIRouter()


# Подключения метода /links
api_router.include_router(
    prefix="/links",
    tags=["links"],
    router=links_router,
)

# Подключения метода /shorten
api_router.include_router(
    prefix="/shorten",
    tags=["shorten"],
    router=shorten_router,
)
