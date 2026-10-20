"""Redis-backed cache for schedule responses."""

import json
import os
import uuid
from typing import Any, Optional

from loguru import logger
from redis.asyncio import Redis


class ScheduleCache:
    """Small Redis adapter that fails open when Redis is unavailable."""

    def __init__(self) -> None:
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ttl = int(os.getenv("REDIS_CACHE_TTL", "2700"))
        self._client: Optional[Redis] = None

    def _get_client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        return self._client

    @staticmethod
    def key(group: int, week: str) -> str:
        return f"medusa:schedule:{group}:{week}"

    @staticmethod
    def week_key(action: str, week: str) -> str:
        return f"medusa:week:{action}:{week}"

    async def get(self, group: int, week: str) -> Optional[dict[str, Any]]:
        try:
            value = await self._get_client().get(self.key(group, week))
            return json.loads(value) if value else None
        except Exception as exc:
            logger.warning(f"Redis cache read failed: {exc}")
            return None

    async def set(self, group: int, week: str, value: dict[str, Any]) -> None:
        try:
            await self._get_client().set(
                self.key(group, week), json.dumps(value), ex=self.ttl
            )
        except Exception as exc:
            logger.warning(f"Redis cache write failed: {exc}")

    async def get_week(self, action: str, week: str) -> Optional[int]:
        try:
            value = await self._get_client().get(self.week_key(action, week))
            return int(value) if value is not None else None
        except Exception as exc:
            logger.warning(f"Redis week cache read failed: {exc}")
            return None

    async def set_week(self, action: str, week: str, value: int) -> None:
        try:
            await self._get_client().set(
                self.week_key(action, week), value, ex=self.ttl
            )
        except Exception as exc:
            logger.warning(f"Redis week cache write failed: {exc}")

    async def allow_request(self, key: str, limit: int, window: int) -> bool:
        """Allow at most ``limit`` requests during a Redis-backed time window."""
        try:
            client = self._get_client()
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, window)
            return count <= limit
        except Exception as exc:
            logger.warning(f"Redis rate limit failed: {exc}")
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def acquire_lock(self, name: str, ttl: int = 5400) -> Optional[str]:
        try:
            token = str(uuid.uuid4())
            acquired = await self._get_client().set(f"medusa:lock:{name}", token, nx=True, ex=ttl)
            return token if acquired else None
        except Exception as exc:
            logger.warning(f"Redis lock failed: {exc}")
            return None

    async def release_lock(self, name: str, token: str) -> None:
        try:
            await self._get_client().eval(
                "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
                1, f"medusa:lock:{name}", token,
            )
        except Exception as exc:
            logger.warning(f"Redis lock release failed: {exc}")


schedule_cache = ScheduleCache()
