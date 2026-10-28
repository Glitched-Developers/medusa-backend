from unittest.mock import AsyncMock, patch

import pytest

from api import _match_teacher_id, resolve_teacher_id

HTML = """
<a href="../teachers/index.php?teacher=105840">Белоусов Николай Иванович</a>
<a href="../teachers/index.php?teacher=128972">Иванов Иван Иванович</a>
"""


def test_match_teacher_prefers_exact_name():
    assert _match_teacher_id(HTML, "Иванов Иван Иванович") == 128972


def test_match_teacher_falls_back_to_first_id():
    assert _match_teacher_id(HTML, "Неизвестное Имя") == 105840


def test_match_teacher_returns_none_when_absent():
    assert _match_teacher_id("<html></html>", "Иванов Иван Иванович") is None


@pytest.mark.asyncio
async def test_resolve_teacher_id_uses_cache():
    with patch("api.schedule_cache.get_teacher", new=AsyncMock(return_value=128972)):
        assert await resolve_teacher_id("Иванов Иван Иванович") == 128972


@pytest.mark.asyncio
async def test_resolve_teacher_id_fetches_and_caches():
    response = AsyncMock()
    response.text = HTML
    response.raise_for_status = lambda: None
    client = AsyncMock()
    client.get.return_value = response
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None

    with (
        patch("api.schedule_cache.get_teacher", new=AsyncMock(return_value=None)),
        patch("api.schedule_cache.set_teacher", new=AsyncMock()) as set_teacher,
        patch("api.httpx.AsyncClient", return_value=client),
    ):
        assert await resolve_teacher_id("Иванов Иван Иванович") == 128972

    set_teacher.assert_awaited_once_with("Иванов Иван Иванович", 128972)


@pytest.mark.asyncio
async def test_resolve_teacher_id_missing():
    response = AsyncMock()
    response.text = "<html></html>"
    response.raise_for_status = lambda: None
    client = AsyncMock()
    client.get.return_value = response
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None

    with (
        patch("api.schedule_cache.get_teacher", new=AsyncMock(return_value=None)),
        patch("api.httpx.AsyncClient", return_value=client),
        pytest.raises(LookupError),
    ):
        await resolve_teacher_id("Никто")
