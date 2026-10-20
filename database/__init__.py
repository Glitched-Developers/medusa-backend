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

import os

from loguru import logger
from sqlalchemy import Column, MetaData, String, Integer, Table, text
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
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
    Column("timestamp", String(8), nullable=False, comment="Last update timestamp"),
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

    Note:
        This function is safe to call multiple times - it won't recreate
        existing valid database structures.
    """
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)

    # PostgreSQL has no local database file. The schema check below works for
    # both supported database backends.
    db_file_exists = not DATABASE_URL.startswith(("sqlite",)) or os.path.exists(
        "./data/Schedules.db"
    )

    if not db_file_exists:
        logger.info("Database file not found. Creating new database...")
        # Create new database from scratch
        async with engine.begin() as conn:
            await conn.run_sync(meta.create_all)
        logger.info("New database created successfully.")
        return

    # Verify existing database structure
    try:
        logger.info("Database file exists. Verifying structure...")
        async with engine.begin() as conn:

            def check_table_exists(connection):
                """Check if schedule_by_groups table exists in database."""
                inspector = inspect(connection)
                return "schedule_by_groups" in inspector.get_table_names()

            table_exists = await conn.run_sync(check_table_exists)

            if not table_exists:
                logger.warning("Table 'schedule_by_groups' missing. Creating...")
                # Create missing table
                await conn.run_sync(meta.create_all)
                logger.info("Table created.")
            else:
                columns = await conn.run_sync(
                    lambda connection: {
                        column["name"]
                        for column in inspect(connection).get_columns(
                            "schedule_by_groups"
                        )
                    }
                )
                if "hash" in columns:
                    logger.info("Removing obsolete hash column from schedule table...")
                    try:
                        await conn.execute(
                            text("ALTER TABLE schedule_by_groups DROP COLUMN hash")
                        )
                    except SQLAlchemyError:
                        logger.warning(
                            "SQLite cannot drop the legacy hash column; "
                            "the application will continue without using it."
                        )
                logger.info("Database structure verified.")

    except SQLAlchemyError as e:
        logger.error(f"Database error during initialization: {e}")
        # Recover from database corruption by recreating structure
        logger.warning("Attempting to recover database...")
        async with engine.begin() as conn:
            await conn.run_sync(meta.drop_all)
            await conn.run_sync(meta.create_all)
        logger.info("Database recovered.")
