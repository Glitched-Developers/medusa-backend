"""Monthly refresh of the auditorium directory."""

import asyncio
import os
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import func, select

from api.auditoriums import fetch_auditorium_directory
from cache import schedule_cache
from database import engine
from database.auditoriums import auditoriums, replace_auditoriums

# 30 days. A restart inside the window does not crawl again: the timestamp
# lives on the rows themselves, so flushing Redis does not trigger a recrawl.
REFRESH_INTERVAL = timedelta(days=int(os.getenv("AUDITORIUM_REFRESH_DAYS", "30")))


def _due(updated_at: datetime | None, now: datetime) -> bool:
    if updated_at is None:
        return True
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return now - updated_at >= REFRESH_INTERVAL


async def latest_refresh() -> datetime | None:
    """When the directory was last written, or None if it is empty."""
    async with engine.connect() as conn:
        return await conn.scalar(select(func.max(auditoriums.c.updated_at)))


async def refresh_auditoriums_if_due(now: datetime | None = None) -> bool:
    """Crawl and replace the directory when the last crawl is a month old.

    Returns True when a crawl was stored. A crawl that fails leaves the
    previous directory in place: ``replace_auditoriums`` only runs after the
    upstream call returns rows.
    """
    now = now or datetime.now(timezone.utc)
    if not _due(await latest_refresh(), now):
        return False

    rows = await fetch_auditorium_directory()
    stored = await replace_auditoriums(rows)
    logger.info(f"Stored {stored} auditoriums")
    return True


async def auditorium_refresh_task():
    """Check once a day whether the monthly auditorium crawl is due."""
    while True:
        try:
            lock = await schedule_cache.acquire_lock("auditorium-refresh", ttl=3600)
            if lock:
                try:
                    await refresh_auditoriums_if_due()
                finally:
                    await schedule_cache.release_lock("auditorium-refresh", lock)
        except Exception as error:
            logger.exception(f"Auditorium refresh failed: {error}")
        await asyncio.sleep(24 * 60 * 60)
