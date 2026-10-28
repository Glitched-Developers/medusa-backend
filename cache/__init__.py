"""Redis-backed cache for schedule responses."""

import json
import os
import uuid
from typing import Any, Optional

from loguru import logger
from redis.asyncio import Redis

from observability.metrics import cache_hits, cache_misses, cache_operations


class ScheduleCache:
    """Small Redis adapter that fails open when Redis is unavailable."""

    def __init__(self) -> None:
        """Create a cache adapter using Redis settings from the environment."""
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ttl = int(os.getenv("REDIS_CACHE_TTL", "2700"))
        self.teacher_ttl = int(os.getenv("REDIS_TEACHER_CACHE_TTL", "604800"))
        self._client: Optional[Redis] = None

    def _get_client(self) -> Redis:
        """Return the lazily initialized asynchronous Redis client."""
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
        """Build the Redis key used for a group's schedule."""
        return f"medusa:schedule:{group}:{week}"

    @staticmethod
    def week_key(action: str, week: str) -> str:
        """Build the Redis key used for a calculated academic week."""
        return f"medusa:week:{action}:{week}"

    @staticmethod
    def teacher_key(full_name: str) -> str:
        """Build the Redis key used for a resolved teacher id."""
        return f"medusa:teacher:{full_name.casefold()}"

    async def get(self, group: int, week: str) -> Optional[dict[str, Any]]:
        """Read a cached schedule, returning ``None`` on a miss or Redis error."""
        try:
            value = await self._get_client().get(self.key(group, week))
            if value:
                cache_operations.labels("schedule_get", "hit").inc()
                cache_hits.labels("schedule").inc()
            else:
                cache_operations.labels("schedule_get", "miss").inc()
                cache_misses.labels("schedule").inc()
            return json.loads(value) if value else None
        except Exception as exc:
            cache_operations.labels("schedule_get", "error").inc()
            logger.warning(f"Redis cache read failed: {exc}")
            return None

    async def set(self, group: int, week: str, value: dict[str, Any]) -> None:
        """Store a schedule in Redis for the configured TTL."""
        try:
            await self._get_client().set(
                self.key(group, week), json.dumps(value), ex=self.ttl
            )
            cache_operations.labels("schedule_set", "success").inc()
        except Exception as exc:
            cache_operations.labels("schedule_set", "error").inc()
            logger.warning(f"Redis cache write failed: {exc}")

    async def get_week(self, action: str, week: str) -> Optional[int]:
        """Read a cached week number, returning ``None`` if unavailable."""
        try:
            value = await self._get_client().get(self.week_key(action, week))
            if value is not None:
                cache_hits.labels("week").inc()
            else:
                cache_misses.labels("week").inc()
            return int(value) if value is not None else None
        except Exception as exc:
            logger.warning(f"Redis week cache read failed: {exc}")
            return None

    async def set_week(self, action: str, week: str, value: int) -> None:
        """Store a calculated week number for the configured TTL."""
        try:
            await self._get_client().set(
                self.week_key(action, week), value, ex=self.ttl
            )
        except Exception as exc:
            logger.warning(f"Redis week cache write failed: {exc}")

    async def get_teacher(self, full_name: str) -> Optional[int]:
        """Read a cached teacher id, returning ``None`` if unavailable."""
        try:
            value = await self._get_client().get(self.teacher_key(full_name))
            if value is not None:
                cache_operations.labels("teacher_get", "hit").inc()
                cache_hits.labels("teacher").inc()
            else:
                cache_operations.labels("teacher_get", "miss").inc()
                cache_misses.labels("teacher").inc()
            return int(value) if value is not None else None
        except Exception as exc:
            cache_operations.labels("teacher_get", "error").inc()
            logger.warning(f"Redis teacher cache read failed: {exc}")
            return None

    async def set_teacher(self, full_name: str, teacher_id: int) -> None:
        """Store a resolved teacher id for the configured TTL."""
        try:
            await self._get_client().set(
                self.teacher_key(full_name), teacher_id, ex=self.teacher_ttl
            )
            cache_operations.labels("teacher_set", "success").inc()
        except Exception as exc:
            cache_operations.labels("teacher_set", "error").inc()
            logger.warning(f"Redis teacher cache write failed: {exc}")

    async def allow_request(self, key: str, limit: int, window: int) -> bool:
        """Allow at most ``limit`` requests during a Redis-backed time window.

        Returns ``False`` when Redis is unavailable so callers fail closed.
        """
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
        """Close the Redis connection and discard the cached client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def acquire_lock(self, name: str, ttl: int = 5400) -> Optional[str]:
        """Acquire a distributed lock and return its owner token if successful."""
        try:
            token = str(uuid.uuid4())
            acquired = await self._get_client().set(
                f"medusa:lock:{name}", token, nx=True, ex=ttl
            )
            return token if acquired else None
        except Exception as exc:
            logger.warning(f"Redis lock failed: {exc}")
            return None

    async def release_lock(self, name: str, token: str) -> None:
        """Release a lock only when it is still owned by ``token``."""
        try:
            await self._get_client().eval(
                "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
                1,
                f"medusa:lock:{name}",
                token,
            )
        except Exception as exc:
            logger.warning(f"Redis lock release failed: {exc}")


schedule_cache = ScheduleCache()
