"""Модуль тестирования удаления ссылки по алиасу."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.services import get_urls_service
from database.models import ShortedUrl


@pytest.mark.asyncio(loop_scope="session")
async def test_api_link_with_existing_alias(
    unauthorized_client: AsyncClient,
    session: AsyncSession,
    existing_shorted_url_for_deleting: ShortedUrl
) -> None:
    """Тестирование DELETE /api/links/{alias} с существующими алиасами."""
    deleted_alias = existing_shorted_url_for_deleting.alias

    response = await unauthorized_client.delete(f"/api/links/{deleted_alias}")
    assert response.status_code == 204

    non_existing_url: ShortedUrl | None = await get_urls_service(session) \
        .get_shorted_url_by_alias(deleted_alias)

    assert non_existing_url is None


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(("alias"), [
    ("PIOEHfowhfiwheifwefwefwefwefwef"),
    ("!!!!"),
])
async def test_api_link_with_non_existing_alias(
    unauthorized_client: AsyncClient,
    alias: str,
) -> None:
    """Тестирование DELETE /api/links/{alias} с несуществующим алиасом."""
    response = await unauthorized_client.delete(f"/api/links/{alias}")
    assert response.status_code == 404
