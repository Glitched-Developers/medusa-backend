"""
Tasks Module

This module provides background task functionality for the Medusa Backend application.
It handles automated schedule updates, data synchronization, and cache management
for BSU schedule data.

Key Features:
- Periodic schedule updates every 90 minutes
- Redis-backed caching with a 45-minute validity period
- Individual group schedule updates on-demand
- Error handling and logging for all operations
"""

import asyncio
import json
from datetime import datetime, timedelta

from database import engine, table
from sqlalchemy import select
from loguru import logger
from api import fetch_schedule


async def check_schedule_update(force_group: int = None) -> dict:
    """
    Check for schedule updates and refresh cached data when necessary.

    This function implements intelligent schedule updating with the following logic:
    1. For specific groups: checks cache validity (45 minutes) and updates if needed
    2. For all groups: iterates through database groups and updates stale data
    3. Updates the persistent schedule snapshot after a refresh

    The function prioritizes performance by using cached data when available
    and only fetching new data when the cache has expired or changes are detected.

    Args:
        force_group (int, optional): Specific BSU group ID to update.
                                   If None, checks all groups in database.

    Returns:
        dict: Dictionary containing schedule data for updated groups.
              Returns empty dict if no updates needed or on error.
              For single group requests, returns the schedule data directly.

    Raises:
        Exception: Logs exceptions but doesn't propagate to maintain service stability

    Example:
        >>> # Update specific group
        >>> schedule = await check_schedule_update(force_group=12345)
        >>>
        >>> # Update all groups
        >>> updates = await check_schedule_update()
    """
    logger.info("Starting schedule update check...")
    result = {}

    if force_group:
        logger.info(f"Force group specified: {force_group}")
        async with engine.connect() as conn:
            # Query existing data for the specified group
            query = select(table.c.group, table.c.data, table.c.timestamp).where(
                table.c.group == force_group
            )
            old_data = (await conn.execute(query)).fetchone()

            if not old_data:
                logger.warning(f"No data found for group {force_group}")
                return {}

            # Unpack database row values
            group_id, data_json, timestamp = old_data

            stored_time = datetime.fromisoformat(timestamp)
            time_difference = datetime.now() - stored_time

            # Use cached data if within 45-minute validity period
            if time_difference < timedelta(minutes=45):
                logger.info(
                    f"Using cached data for group {force_group}, last updated {stored_time}"
                )
                try:
                    # Validate and return cached JSON data
                    if data_json and isinstance(data_json, str):
                        return json.loads(data_json)
                    else:
                        logger.error(
                            f"Invalid JSON data for group {force_group}: {data_json}"
                        )
                        return {}
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON for group {force_group}: {e}")
                    logger.debug(f"Invalid JSON data: '{data_json}'")
                    return {}
            else:
                try:
                    # Fetch fresh schedule data from external source
                    new_data = await fetch_schedule(group=force_group)
                    logger.debug(f"Fetched new data for group {force_group}")

                    # Validate received data structure
                    if not new_data or "schedule" not in new_data:
                        logger.error(
                            f"Invalid schedule data received for group {force_group}"
                        )
                        return {}

                    await conn.execute(
                        table.update()
                        .where(table.c.group == force_group)
                        .values(
                            data=json.dumps(new_data["schedule"]),
                            timestamp=new_data["metadata"]["timestamp"],
                        )
                    )
                    await conn.commit()
                    logger.info(f"Updated schedule for group {force_group}")
                    return new_data["schedule"]
                except Exception as e:
                    logger.exception(
                        f"Error processing schedule for group {force_group}: {e}"
                    )
                    return {}

    else:
        # Process all groups in database
        logger.info("Fetching group list from the database...")
        try:
            async with engine.connect() as conn:
                group_list = (await conn.execute(select(table.c.group))).fetchall()

            if not group_list:
                logger.warning("No groups found in database")
                return {}

            logger.info(f"Retrieved groups: {group_list}")

            # Process each group individually
            for group_tuple in group_list:
                group = group_tuple[0]
                try:
                    logger.info(f"Checking schedule for group {group}...")
                    async with engine.connect() as conn:
                        # Query existing data for current group
                        query = select(
                            table.c.group, table.c.data, table.c.timestamp
                        ).where(table.c.group == group)
                        old_data = (await conn.execute(query)).fetchone()

                        if not old_data:
                            logger.warning(f"No data found for group {group}")
                            continue

                        # Unpack database row values
                        group_id, data_json, timestamp = old_data

                        stored_time = datetime.fromisoformat(timestamp)
                        current_time = datetime.now()
                        time_difference = current_time - stored_time

                        # Skip if data is fresh (within 45-minute cache period)
                        if time_difference < timedelta(minutes=45):
                            logger.info(
                                f"Using cached data for group {group}, last updated {stored_time}"
                            )
                            # Safely parse cached data
                            try:
                                if data_json and isinstance(data_json, str):
                                    result[group] = json.loads(data_json)
                                else:
                                    logger.warning(
                                        f"Invalid data format for group {group}"
                                    )
                            except json.JSONDecodeError as e:
                                logger.error(
                                    f"JSON decode error for group {group}: {e}"
                                )
                                logger.debug(f"Invalid JSON: '{data_json}'")
                            continue

                        # Fetch fresh data for stale cache
                        new_data = await fetch_schedule(group=group)

                        if not new_data or "schedule" not in new_data:
                            logger.error(
                                f"Invalid schedule data received for group {group}"
                            )
                            continue

                        await conn.execute(
                            table.update()
                            .where(table.c.group == group)
                            .values(
                                data=json.dumps(new_data["schedule"]),
                                timestamp=new_data["metadata"]["timestamp"],
                            )
                        )
                        await conn.commit()
                        logger.info(f"Updated schedule for group {group}")
                        result[group] = new_data["schedule"]

                except Exception as e:
                    logger.exception(f"Error processing group {group}: {e}")

        except Exception as e:
            logger.exception(f"Error fetching group list: {e}")
            return {}

    return result


async def schedule_update_task():
    """
    Background task for periodic schedule updates.

    This function runs continuously as a background task, updating all schedules
    every 90 minutes to keep the database synchronized with BSU's schedule system.
    It handles errors gracefully to ensure the task continues running even if
    individual updates fail.

    The task performs the following operations:
    1. Runs check_schedule_update() for all groups in the database
    2. Logs the start and completion of each update cycle
    3. Handles and logs any exceptions without stopping the task
    4. Waits 90 minutes between update cycles

    This task is started automatically when the application launches and runs
    for the entire application lifetime.

    Note:
        This function runs indefinitely in a loop. It should only be started
        once as a background task during application startup.

    Example:
        >>> # Started automatically in main.py
        >>> asyncio.create_task(schedule_update_task())
    """
    UPDATE_INTERVAL_MINUTES = 90

    while True:
        try:
            logger.info("Starting scheduled schedule update")
            await check_schedule_update()
            logger.info("Scheduled schedule update completed")
        except Exception as e:
            logger.exception(f"Error during scheduled schedule update: {e}")

        # Wait 90 minutes before next update cycle
        logger.info(f"Next schedule update in {UPDATE_INTERVAL_MINUTES} minutes")
        await asyncio.sleep(UPDATE_INTERVAL_MINUTES * 60)
