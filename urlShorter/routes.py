"""Модуль метода / ."""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AliasNotFoundException
from core.services import get_urls_service
from database.database import get_db
from database.models import ShortedUrl

main_router = APIRouter()


@main_router.get("/{alias}", status_code=301)
async def get_shorted_url(
    alias: str,
    db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    """Переход по короткой ссылке.

    Args:
        alias (str): Алиас короткой ссылки.
        db (AsyncSession, optional): Сессия базы данных. Defaults to Depends(get_db).

    Raises:
        AliasNotFoundException: Если alias не найден (404).

    Returns:
        RedirectResponse: Редирект на оригинальный url.

    """
    urls_service = get_urls_service(db)
    shorted_url: ShortedUrl | None = await urls_service.get_shorted_url_by_alias(alias)

    # Если не нашлась коротка ссылка с данным алиасом
    if shorted_url is None:
        raise AliasNotFoundException

    # В идеале использовать celery для добавления к количеству кликов.
    # Так как при падении приложения celery сохранит таску и сможет к ней вернуться.
    # Но это требует большего времени и настройки.
    # Проблема asyncio.create_task в том,
    # что сессия базы данных закрывается при тестировании, поэтому просто добавим клик.
    await urls_service.add_click_to_shorted_url(shorted_url)
    # Возможно при огромном количестве запросов лучше будет перейти на логику:
    # Сбор кликов в памяти Redis, затем каждые N миллисекунд отправлять их в clickhouse.

    return RedirectResponse(shorted_url.original_url, status_code=301)
