"""Модуль метода /shorten ."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import USER_CREATE_URL_IN_MINUTE_LIMIT
from core.exceptions import (
    InvalidConnectingClientException,
    ShortUrlCreatingException,
    UserCreateUrlLimitExceedException,
)
from core.schemas import CreatedShortedUrlResponseSchema, ShortUrlRequestSchema
from core.services import get_urls_service
from database.database import get_db
from database.models import ShortedUrl

shorten_router = APIRouter()


@shorten_router.post("", status_code=200)
async def create_shorted_url(request: Request,
                             shorted_url_data: ShortUrlRequestSchema,
                             db: AsyncSession = Depends(get_db)
) -> CreatedShortedUrlResponseSchema:
    """Создание короткой ссылки.

    Args:
        request (Request, optional): request запроса.
        shorted_url_data (ShortUrlRequestSchema, optional): Тело запроса.
        db (AsyncSession, optional): Сессия базы данных. Defaults to Depends(get_db).

    Raises:
        InvalidConnectingClientException: Если client не найден (500).
        UserCreateUrlLimitExceedException: Превышен лимит создания ссылок (429).
        ShortUrlCreatingException: Невалидные поля при создании ссылки (400).

    Returns:
        CreatedShortedUrlResponseSchema: Информацию о созданной ссылке.

    """
    client = request.client

    if client is None:
        raise InvalidConnectingClientException

    client_ip: str = client.host

    urls_service = get_urls_service(db)

    created_urls_after_time: datetime = datetime.now() - timedelta(minutes=1)
    client_created_urls_count: int = (
        await urls_service.get_ip_shorted_urls_created_count(
            client_ip, created_urls_after_time
        )
    )

    if client_created_urls_count >= USER_CREATE_URL_IN_MINUTE_LIMIT:
        raise UserCreateUrlLimitExceedException

    try:
        shorted_url: ShortedUrl = await urls_service.create_new_url_with_lock(
            shorted_url_data.url, shorted_url_data.custom_alias, client_ip
        )
    except ValueError as e:
        raise ShortUrlCreatingException(str(e))

    return CreatedShortedUrlResponseSchema(alias=shorted_url.alias)
