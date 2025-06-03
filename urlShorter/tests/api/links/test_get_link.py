"""Модуль тестирования получения информации о ссылке по алиасу."""
import pytest
from httpx import AsyncClient

from database.models import ShortedUrl


@pytest.mark.asyncio(loop_scope="session")
async def test_api_link_with_existing_alias(
    unauthorized_client: AsyncClient,
    existing_shorted_url: ShortedUrl
) -> None:
    """Тестирование GET /api/links/{alias} с существующими алиасами."""
    response = await unauthorized_client.get(f"/api/links/{existing_shorted_url.alias}")
    response_json = response.json()

    assert response.status_code == 200
    assert all(field in response_json
               for field in ("clicks", "created_at", "original_url"))
    assert response_json["clicks"] == existing_shorted_url.clicks
    assert response_json["original_url"] == existing_shorted_url.original_url


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(("alias"), [
    ("PIOEHfowhfiwheifwefwefwefwefwef"),
    ("!!!!"),
])
async def test_api_link_with_non_existing_alias(
    unauthorized_client: AsyncClient,
    alias: str,
) -> None:
    """Тестирование GET /api/links/{alias} с несуществующим алиасом."""
    response = await unauthorized_client.get(f"/api/links/{alias}")
    assert response.status_code == 404
