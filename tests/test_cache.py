import json
from unittest.mock import AsyncMock, patch

import pytest

from cache import ScheduleCache


@pytest.mark.asyncio
async def test_schedule_cache_get_and_set():
    cache = ScheduleCache()
    client = AsyncMock()
    client.get.return_value = json.dumps({"schedule": {}})

    with patch.object(cache, "_get_client", return_value=client):
        assert await cache.get(123, "week") == {"schedule": {}}
        await cache.set(123, "week", {"schedule": {}})

    client.set.assert_awaited_once()
    assert client.set.await_args.kwargs["ex"] == cache.ttl


@pytest.mark.asyncio
async def test_schedule_cache_fails_open_on_redis_error():
    cache = ScheduleCache()
    client = AsyncMock()
    client.get.side_effect = ConnectionError("Redis unavailable")

    with patch.object(cache, "_get_client", return_value=client):
        assert await cache.get(123, "week") is None


@pytest.mark.asyncio
async def test_week_cache_round_trip():
    cache = ScheduleCache()
    client = AsyncMock()
    client.get.return_value = "42"

    with patch.object(cache, "_get_client", return_value=client):
        assert await cache.get_week("this_week", "0") == 42
        await cache.set_week("this_week", "0", 42)

    client.set.assert_awaited_once()
