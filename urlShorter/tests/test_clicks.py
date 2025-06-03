"""Модуль тестирования переходов по ссылке."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ShortedUrl


@pytest.mark.asyncio(loop_scope="session")
async def test_goto_existing_shorted_url(
    unauthorized_client: AsyncClient,
    session: AsyncSession,
    existing_shorted_url: ShortedUrl,
) -> None:
    """Тестирование GET /{alias} с существующими ссылками."""
    response = await unauthorized_client.get(existing_shorted_url.alias)
    assert response.status_code == 301
    # Будет работать проверка до тех пор, пока не использован celery
    # или любое другое решение, негарантирующее законченность добавления клика
    # при переходе в момент проверки.
    await session.refresh(existing_shorted_url)
    assert existing_shorted_url.clicks == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_goto_non_exist_url(
    unauthorized_client: AsyncClient,
) -> None:
    """Тестирование GET /{alias} с несуществующей ссылкой."""
    response = await unauthorized_client.get(",,,,,")
    assert response.status_code == 404
