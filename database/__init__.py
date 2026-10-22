"""
Database Module

This module handles database operations for the Medusa Backend application.
It manages SQLite database connections and provides the schedule_by_groups table
for storing BSU schedule data.

Database Schema:
    schedule_by_groups:
        - group (Integer, PK): BSU group ID
        - data (String): JSON schedule data
        - timestamp (String): Last update timestamp
"""

import json
import os
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, select
from sqlalchemy.ext.asyncio import create_async_engine

# Database configuration
meta = MetaData()
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/Schedules.db",
)

# Async SQLite engine for concurrent operations
engine = create_async_engine(DATABASE_URL, echo=False)

# Schedule storage table definition
table = Table(
    "schedule_by_groups",
    meta,
    Column("group", Integer, primary_key=True, comment="BSU group ID"),
    Column("data", String(), nullable=False, comment="JSON schedule data"),
    Column(
        "timestamp",
        DateTime(timezone=True),
        nullable=False,
        comment="Last update timestamp",
    ),
)

from database.mail import user_devices, user_mail_accounts  # noqa: E402


async def save_schedule(group: int, schedule_data: dict) -> None:
    """Insert or update a group's schedule snapshot.

    Args:
        group: BSU group identifier used as the primary key.
        schedule_data: Parsed response containing ``metadata.timestamp`` and
            ``schedule`` fields.

    Raises:
        ValueError: If required response fields are missing.
    """
    metadata = schedule_data.get("metadata", {})
    timestamp = metadata.get("timestamp")
    schedule = schedule_data.get("schedule")
    if not timestamp or schedule is None:
        raise ValueError("Schedule response is missing metadata.timestamp or schedule")

    async with engine.begin() as conn:
        exists = await conn.scalar(select(table.c.group).where(table.c.group == group))
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed_timestamp.tzinfo is None:
            parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)
        values = {"data": json.dumps(schedule), "timestamp": parsed_timestamp}
        if exists is None:
            await conn.execute(table.insert().values(group=group, **values))
        else:
            await conn.execute(
                table.update().where(table.c.group == group).values(**values)
            )


async def init_database() -> None:
    """
    Initialize the SQLite database and create required tables.

    This function performs database initialization with the following logic:
    1. If database file doesn't exist, creates new database with tables
    2. If database exists, verifies table structure and creates missing tables
    3. In case of errors, recreates the entire database structure

    The function ensures the schedule_by_groups table exists with proper schema
    for storing BSU schedule data.

    Raises:
        SQLAlchemyError: If database operations fail during initialization
        ValueError: If database schema version does not match expected version

    Note:
        This function is safe to call multiple times - it won't recreate
        existing valid database structures.
    """
    # Schema changes are managed exclusively by Alembic.
    os.makedirs("./data", exist_ok=True)
    async with engine.connect() as conn:
        await conn.execute(select(1))
    logger.info("Database connection verified.")

    # Verify database schema version
    await verify_database_schema()


async def verify_database_schema() -> None:
    """
    Verify that the database schema matches the expected version.

    Checks the alembic_version table to ensure migrations are up-to-date.

    Raises:
        ValueError: If schema version does not match expected version or if alembic_version table is missing
    """
    expected_revision = "0004"  # Latest migration revision

    try:
        from sqlalchemy import text

        async with engine.connect() as conn:
            # Query current schema version from alembic_version table
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()

            if row is None:
                logger.warning("No schema version found in alembic_version table")
                raise ValueError(
                    "Database schema version not found. Please run migrations: alembic upgrade head"
                )

            current_revision = row[0]

            if current_revision != expected_revision:
                logger.error(
                    f"Database schema mismatch: expected {expected_revision}, found {current_revision}"
                )
                raise ValueError(
                    f"Database schema version mismatch. Expected: {expected_revision}, Found: {current_revision}. "
                    f"Please run migrations: alembic upgrade head"
                )

            logger.info(f"Database schema version verified: {current_revision}")

    except Exception as e:
        error_message = str(e).lower()
        if "no such table" in error_message and "alembic_version" in error_message:
            logger.error(
                "alembic_version table does not exist - database is not initialized"
            )
            raise ValueError(
                "Database is not initialized. Please run migrations: alembic upgrade head"
            ) from e
        raise


__all__ = ["engine", "meta", "table", "user_devices", "user_mail_accounts"]
