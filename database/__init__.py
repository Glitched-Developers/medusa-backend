import os

from sqlalchemy import Column, MetaData, String, Integer, Table
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

meta = MetaData()
DATABASE_URL = "sqlite+aiosqlite:///Schedules.db"

engine = create_async_engine(DATABASE_URL, echo=False)

table = Table("schedule_by_groups", meta,
          Column("group", Integer, primary_key=True),
          Column("hash", String(128), nullable=False),
          Column("data", String(), nullable=False),
          Column("timestamp", String(8), nullable=False),
        )

async def init_database() -> None:
    """
    Initializes the database. If the database file does not exist, it creates a new database.
    If the database file exists, it checks for the existence of the required table and creates it if necessary.
    If an error occurs, the database structure is recreated.

    Raises:
        SQLAlchemyError: If there is an issue with the database operations.
    """
    # Check if the database file exists
    db_file_exists = os.path.exists("Schedules.db")

    if not db_file_exists:
        # If the file does not exist, create the database from scratch
        async with engine.begin() as conn:
            await conn.run_sync(meta.create_all)
        return

    # If the file exists, check for the existence of the table
    try:
        # Check for the existence of the table using SQLAlchemy inspector
        async with engine.begin() as conn:
            # Use SQLAlchemy inspector to verify if the table exists
            def check_table_exists(connection):
                inspector = inspect(connection)
                return "schedule_by_groups" in inspector.get_table_names()

            table_exists = await conn.run_sync(check_table_exists)

            if not table_exists:
                # If the table does not exist, create it
                await conn.run_sync(meta.create_all)
            # If the table exists, do nothing
    except SQLAlchemyError:
        # In case of an error, recreate the database structure
        async with engine.begin() as conn:
            await conn.run_sync(meta.drop_all)
            await conn.run_sync(meta.create_all)