"""Модуль метода /links ."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AliasNotFoundException
from core.schemas import ShortedUrlDetailResponseSchema, ShortedUrlResponseSchema
from core.services import get_urls_service
from database.database import get_db
from database.models import ShortedUrl

links_router = APIRouter()


@links_router.get("", status_code=200)
async def get_links(
    page: int = 0,
    per_page: int = 10,
    db: AsyncSession = Depends(get_db)
) -> list[ShortedUrlResponseSchema]:
    """Получение инфомрации ссылок на странице.

    Args:
        page (int, optional): Номер страницы. Defaults to 0.
        per_page (int, optional): Количество ссылок на страницу. Defaults to 10.
        db (AsyncSession, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        list[ShortedUrlResponseSchema]: Список информации ссылок на странице.

    """
    shorted_urls: list[ShortedUrl] = (
        await get_urls_service(db).get_shorted_urls(page, per_page)
    )

    return [ShortedUrlResponseSchema.model_validate(shorted_url)
            for shorted_url in shorted_urls]


@links_router.get("/{alias}", status_code=200)
async def get_link(
    alias: str,
    db: AsyncSession = Depends(get_db)
) -> ShortedUrlDetailResponseSchema:
    """Получение информации о ссылке по alias'у.

    Args:
        alias (str): alias ссылки
        db (AsyncSession, optional): Сессия базы данных. Defaults to Depends(get_db).

    Raises:
        AliasNotFoundException: Если alias не найден (404).

    Returns:
        ShortedUrlDetailResponseSchema: Информация о ссылке по alias'у.

    """
    shorted_url: ShortedUrl | None = (
        await get_urls_service(db).get_shorted_url_by_alias(alias)
    )

    if shorted_url is None:
        raise AliasNotFoundException

    return ShortedUrlDetailResponseSchema.model_validate(shorted_url)


@links_router.delete("/{alias}", status_code=204)
async def delete_link(alias: str, db: AsyncSession = Depends(get_db)) -> None:
    """Удаление ссылки по alias'у.

    Args:
        alias (str): alias ссылки.
        db (AsyncSession, optional): Сессия базы данных. Defaults to Depends(get_db).

    Raises:
        AliasNotFoundException: Если alias не найден (404).

    """
    urls_service = get_urls_service(db)
    shorted_url: ShortedUrl | None = await urls_service.get_shorted_url_by_alias(alias)

    if shorted_url is None:
        raise AliasNotFoundException

    await urls_service.delete_url_by_alias_with_lock(alias)
