"""Модуль тестирования получения списка ссылок."""
import pytest
from httpx import AsyncClient

from core.config import MAX_PER_PAGE_URLS_COUNT
from database.models import ShortedUrl


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(("page", "per_page"), [
    (-1, 30),
    (0, 30),
    (0, 60),
    (1, 30),
    (1, 60),
    (2, 30),
])
async def test_api_links_alias(
    unauthorized_client: AsyncClient,
    existing_shorted_url_for_get_links: list[ShortedUrl],
    page: int,
    per_page: int,
) -> None:
    """Тестирование GET /api/links с существующими алиасами."""
    response = await unauthorized_client \
        .get(f"/api/links?page={page}&per_page={per_page}")
    response_json = response.json()

    assert response.status_code == 200

    assert isinstance(response_json, list)

    assert len(response_json) == min(# type: ignore
        per_page,
        MAX_PER_PAGE_URLS_COUNT,
        len(existing_shorted_url_for_get_links) - (max(page - 1, 0) * per_page)
    )

    assert all(field in response_json[0]
               for field in ("alias", "clicks", "created_at", "original_url"))


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(("page", "per_page"), [
    (-1, None),
    (None, -1),
    (None, None),
])
async def test_api_links_alias_unproccessable_entity(
    unauthorized_client: AsyncClient,
    page: int | None,
    per_page: int | None,
) -> None:
    """Тестирование GET /api/links с некорретным телом."""
    response = await unauthorized_client \
        .get(f"/api/links?page={page}&per_page={per_page}")
    assert response.status_code == 422


