"""
Database Module

This module handles database operations for the Medusa Backend application.
It manages SQLite database connections and provides the schedule_by_groups table
for storing BSU schedule data with hash-based change detection.

Database Schema:
    schedule_by_groups:
        - group (Integer, PK): BSU group ID
        - hash (String): Content hash for change detection
        - data (String): JSON schedule data
        - timestamp (String): Last update timestamp
"""

import os

from sqlalchemy import Column, MetaData, String, Integer, Table
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

# Database configuration
meta = MetaData()
DATABASE_URL = "sqlite+aiosqlite:///Schedules.db"

# Async SQLite engine for concurrent operations
engine = create_async_engine(DATABASE_URL, echo=False)

# Schedule storage table definition
table = Table(
    "schedule_by_groups", 
    meta,
    Column("group", Integer, primary_key=True, comment="BSU group ID"),
    Column("hash", String(128), nullable=False, comment="Content hash for change detection"),
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
    for storing BSU schedule data with hash-based change detection.
    
    Raises:
        SQLAlchemyError: If database operations fail during initialization
        
    Note:
        This function is safe to call multiple times - it won't recreate
        existing valid database structures.
    """
    # Check if the database file exists on filesystem
    db_file_exists = os.path.exists("Schedules.db")

    if not db_file_exists:
        # Create new database from scratch
        async with engine.begin() as conn:
            await conn.run_sync(meta.create_all)
        return

    # Verify existing database structure
    try:
        async with engine.begin() as conn:
            def check_table_exists(connection):
                """Check if schedule_by_groups table exists in database."""
                inspector = inspect(connection)
                return "schedule_by_groups" in inspector.get_table_names()

            table_exists = await conn.run_sync(check_table_exists)

            if not table_exists:
                # Create missing table
                await conn.run_sync(meta.create_all)
                
    except SQLAlchemyError:
        # Recover from database corruption by recreating structure
        async with engine.begin() as conn:
            await conn.run_sync(meta.drop_all)
            await conn.run_sync(meta.create_all)