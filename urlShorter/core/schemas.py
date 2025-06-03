"""Модуль кастомных шаблонов pydantic."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.config import BASE_URL

SHORT_URL_SCHEMA = BASE_URL + "{}"


class BaseSchema(BaseModel):
    """Базовая схема для всех схем приложения."""

    model_config = ConfigDict(from_attributes=True)


class ShortUrlRequestSchema(BaseSchema):
    """Схема получения информации о создаваемой ссылке от клиента."""

    url: str
    custom_alias: str | None = None


class CreatedShortedUrlResponseSchema(BaseSchema):
    """Схема отправки информации о созданной ссылке клиенту."""

    alias: str
    short_url: str = Field(default_factory=lambda data: SHORT_URL_SCHEMA.format(
        data["alias"]
    ))


class ShortedUrlDetailResponseSchema(BaseSchema):
    """Схема отправки информации о существующей ссылке клиенту."""

    original_url: str
    created_at: datetime
    clicks: int


class ShortedUrlResponseSchema(BaseSchema):
    """Схема отправки информации об одной из существующих ссылокй клиенту."""

    original_url: str
    alias: str
    clicks: int
    created_at: datetime
