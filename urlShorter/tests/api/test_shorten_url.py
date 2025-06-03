"""Модуль тестирования создания укороченных ссылок."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.services import get_urls_service
from database.models import ShortedUrl


@pytest.mark.asyncio(loop_scope="session")
async def test_api_shorten_fail_alias_taken(
    unauthorized_client: AsyncClient,
    existing_shorted_url: ShortedUrl,
) -> None:
    """Тестирование POST /api/shorten с занятыми алиасами."""
    data: dict[str, str | None] = {
        "url": "https://AnyUrl.com/",
        "custom_alias": existing_shorted_url.alias
    }

    response = await unauthorized_client.post("/api/shorten", json=data)
    assert response.status_code == 400


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("data", [
    ({"url": None}),
    ({"custom_alias": "hhhhh"}),
    ({"custom_alias": ""}),
])
async def test_api_shorten_fail_unproccessable_entity(
    unauthorized_client: AsyncClient,
    data: dict[str, str | None],
) -> None:
    """Тестирование POST /api/shorten с некорректным телом запроса."""
    response = await unauthorized_client.post("/api/shorten", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("data", [
    ({"url": "", "custom_alias": "AAAA"}),
    ({"url": "https://", "custom_alias": "AAAA"}),
    ({"url": "https://" + "12" * 5000, "custom_alias": "AAAA"}),
    ({"url": "https://CorrectOk.com/", "custom_alias": ""}),
    ({"url": "https://CorrectOk.com/", "custom_alias": "AAA"}),
    ({"url": "https://CorrectOk.com/", "custom_alias": "A" * 50}),
    ({"url": "https://CorrectOk.com/", "custom_alias": ",,,,"}),
])
async def test_api_shorten_fail_incorrect_url_or_custom_alias(
    unauthorized_client: AsyncClient,
    data: dict[str, str | None],
) -> None:
    """Тестирование POST /api/shorten с некорректным телом запроса."""
    response = await unauthorized_client.post("/api/shorten", json=data)
    assert response.status_code == 400


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(("url", "custom_alias"), [
    ("https://wikipedia.ru/", "QQQQ"),
    ("https://wikipedia.ru/", None),
    ("http://footbal/", "AAAAA--q0"),
    ("http://smile.com/", None),
    ("http://smile.repeat.com/", None),
])
async def test_api_shorten_success(
    unauthorized_client: AsyncClient,
    session: AsyncSession,
    url: str,
    custom_alias: str | None,
) -> None:
    """Тестирование POST /api/shorten с успешным созданием ссылок."""
    data: dict[str, str | None] = {
        "url": url,
        "custom_alias": custom_alias
    }

    response = await unauthorized_client.post("/api/shorten", json=data)
    response_json = response.json()

    assert response.status_code == 200
    assert all(field in response_json for field in ("alias", "short_url"))

    shorted_url_alias = response_json["alias"]

    if custom_alias is not None:
        assert shorted_url_alias == custom_alias

    shorted_url: ShortedUrl | None = await get_urls_service(session) \
        .get_shorted_url_by_alias(shorted_url_alias)

    assert isinstance(shorted_url, ShortedUrl)

    assert shorted_url.original_url == url
    assert shorted_url.alias == shorted_url_alias
    assert shorted_url.clicks == 0


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(("url", "custom_alias"), [
    ("https://wikipedia.ru/", "QQQQ"),
    ("https://wikipedia.ru/", None),
    ("http://footbal/", "AAAAA--q0"),
    ("http://smile.com/", None),
    ("http://smile.repeat.com/", None),
])
async def test_api_shorten_limit_exceeded(
    unauthorized_client: AsyncClient,
    url: str,
    custom_alias: str | None,
) -> None:
    """Тестирование POST /api/shorten с выходом за рамки лимита."""
    data: dict[str, str | None] = {
        "url": url,
        "custom_alias": custom_alias
    }

    response = await unauthorized_client.post("/api/shorten", json=data)

    assert response.status_code == 429
