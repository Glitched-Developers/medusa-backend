"""Persistence for the BSU auditorium directory."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, MetaData, String, Table, select

from database import engine

meta = MetaData()

auditoriums = Table(
    "auditoriums",
    meta,
    Column("id", String(32), primary_key=True, comment="BSU auditorium id"),
    Column("name", String(255), nullable=False, comment="Name as published by BSU"),
    Column("token", String(64), nullable=False, comment="Normalized room token"),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        comment="When this row was last seen during a crawl",
    ),
)


async def replace_auditoriums(rows: list[dict]) -> int:
    """Replace the directory with a fresh crawl.

    An empty crawl is refused so a failed upstream pass cannot wipe the map.
    """
    if not rows:
        raise ValueError("Refusing to replace auditoriums with an empty crawl")

    now = datetime.now(timezone.utc)
    payload = [{**row, "updated_at": now} for row in rows]
    async with engine.begin() as conn:
        await conn.execute(auditoriums.delete())
        await conn.execute(auditoriums.insert(), payload)
    return len(payload)


async def list_auditoriums() -> list[dict]:
    """Return every stored auditorium, ordered by its normalized token."""
    async with engine.connect() as conn:
        result = await conn.execute(
            select(
                auditoriums.c.id,
                auditoriums.c.name,
                auditoriums.c.token,
            ).order_by(auditoriums.c.token, auditoriums.c.id)
        )
        return [dict(row._mapping) for row in result.fetchall()]


async def get_auditorium(auditorium_id: str) -> dict | None:
    """Return one auditorium, or None when the id is not in the directory."""
    async with engine.connect() as conn:
        result = await conn.execute(
            select(
                auditoriums.c.id,
                auditoriums.c.name,
                auditoriums.c.token,
            ).where(auditoriums.c.id == auditorium_id)
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None
