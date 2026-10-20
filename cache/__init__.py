"""Redis-backed cache for schedule responses."""

import json
import os
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

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def acquire_lock(self, name: str, ttl: int = 5400) -> bool:
        try:
            return bool(await self._get_client().set(f"medusa:lock:{name}", "1", nx=True, ex=ttl))
        except Exception as exc:
            logger.warning(f"Redis lock failed: {exc}")
            return True

    async def release_lock(self, name: str) -> None:
        try:
            await self._get_client().delete(f"medusa:lock:{name}")
        except Exception as exc:
            logger.warning(f"Redis lock release failed: {exc}")


schedule_cache = ScheduleCache()
