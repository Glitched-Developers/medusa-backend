import pytest

from cache import ScheduleCache


@pytest.mark.asyncio
async def test_lock_uses_token_and_owner_safe_release(monkeypatch):
    cache = ScheduleCache()

    class FakeRedis:
        async def set(self, *args, **kwargs):
            return True

        async def eval(self, *args):
            return 1

    monkeypatch.setattr(cache, "_get_client", lambda: FakeRedis())
    token = await cache.acquire_lock("dev_test")
    assert token
    await cache.release_lock("dev_test", token)


@pytest.mark.asyncio
async def test_rate_limit_rejects_after_limit(monkeypatch):
    cache = ScheduleCache()
    count = 0

    class FakeRedis:
        async def incr(self, key):
            nonlocal count
            count += 1
            return count

        async def expire(self, key, window):
            return True

    monkeypatch.setattr(cache, "_get_client", lambda: FakeRedis())
    assert await cache.allow_request("key", 1, 60)
    assert not await cache.allow_request("key", 1, 60)
