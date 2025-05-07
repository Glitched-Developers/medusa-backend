import asyncio
import json

from database import engine, table
from sqlalchemy import select
from loguru import logger
import hash_utils
from api import fetch_schedule


async def check_schedule_update(force_group: int = None) -> dict or None:
    """
    Проверяет обновления расписания.

    Функция получает список групп из базы данных, запрашивает последние расписания
    для каждой группы и сравнивает их с существующими данными. При изменении
    обновляет базу данных.

    Args:
        force_group: Опциональный ID группы для принудительного обновления

    Returns:
        Словарь с данными расписания или None при ошибке
    """
    logger.info("Starting schedule update check...")
    from datetime import datetime, timedelta
    result = {}

    if force_group:
        logger.info(f"Force group specified: {force_group}")
        async with engine.connect() as conn:
            # Исправленный синтаксис select
            query = select(
                table.c.group,
                table.c.data,
                table.c.hash,
                table.c.timestamp
            ).where(table.c.group == force_group)
            old_data = (await conn.execute(query)).fetchone()

            if not old_data:
                logger.warning(f"No data found for group {force_group}")
                return None

            # Распаковка значений с понятными именами
            group_id, data_json, data_hash, timestamp = old_data

            stored_time = datetime.fromisoformat(timestamp)
            time_difference = datetime.now() - stored_time

            if time_difference < timedelta(minutes=45):
                logger.info(f"Using cached data for group {force_group}, last updated {stored_time}")
                try:
                    # Проверка валидности JSON перед возвратом
                    if data_json and isinstance(data_json, str):
                        return json.loads(data_json)
                    else:
                        logger.error(f"Invalid JSON data for group {force_group}: {data_json}")
                        return None
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON for group {force_group}: {e}")
                    logger.debug(f"Invalid JSON data: '{data_json}'")
                    return None
            else:
                try:
                    new_data = await fetch_schedule(group=force_group)
                    logger.debug(f"Fetched new data for group {force_group}")

                    # Валидация полученных данных
                    if not new_data or "schedule" not in new_data:
                        logger.error(f"Invalid schedule data received for group {force_group}")
                        return None

                    if hash_utils.check_hash(new_data["schedule"], data_hash) is False:
                        # Update the database with the new data
                        await conn.execute(table.update().where(table.c.group == force_group).values(
                            data=json.dumps(new_data["schedule"]),
                            hash=hash_utils.get_hash(json.dumps(new_data["schedule"])),
                            timestamp=new_data["metadata"]["timestamp"]
                        ))
                        await conn.commit()

                        logger.info(f"Updated schedule for group {force_group}")
                        return new_data["schedule"]
                    else:
                        logger.info(f"No changes detected for group {force_group}, using existing data")
                        return json.loads(data_json)
                except Exception as e:
                    logger.exception(f"Error processing schedule for group {force_group}: {e}")
                    return None

    else:
        logger.info("Fetching group list from the database...")
        try:
            async with engine.connect() as conn:
                group_list = (await conn.execute(select(table.c.group))).fetchall()

            if not group_list:
                logger.warning("No groups found in database")
                return {}

            logger.info(f"Retrieved groups: {group_list}")

            # Обработка для каждой группы
            for group_tuple in group_list:
                group = group_tuple[0]
                try:
                    logger.info(f"Checking schedule for group {group}...")
                    async with engine.connect() as conn:
                        # Исправленный синтаксис select
                        query = select(
                            table.c.group,
                            table.c.data,
                            table.c.hash,
                            table.c.timestamp
                        ).where(table.c.group == group)
                        old_data = (await conn.execute(query)).fetchone()

                        if not old_data:
                            logger.warning(f"No data found for group {group}")
                            continue

                        # Распаковка значений
                        group_id, data_json, data_hash, timestamp = old_data

                        stored_time = datetime.fromisoformat(timestamp)
                        current_time = datetime.now()
                        time_difference = current_time - stored_time

                        if time_difference < timedelta(minutes=45):
                            logger.info(f"Using cached data for group {group}, last updated {stored_time}")
                            # Безопасное получение данных
                            try:
                                if data_json and isinstance(data_json, str):
                                    result[group] = json.loads(data_json)
                                else:
                                    logger.warning(f"Invalid data format for group {group}")
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error for group {group}: {e}")
                                logger.debug(f"Invalid JSON: '{data_json}'")
                            continue

                        # Получение новых данных
                        new_data = await fetch_schedule(group=group)

                        if not new_data or "schedule" not in new_data:
                            logger.error(f"Invalid schedule data received for group {group}")
                            continue

                        if hash_utils.check_hash(new_data["schedule"], data_hash) is False:
                            await conn.execute(table.update().where(table.c.group == group).values(
                                data=json.dumps(new_data["schedule"]),
                                hash=hash_utils.get_hash(json.dumps(new_data["schedule"])),
                                timestamp=new_data["metadata"]["timestamp"]
                            ))
                            await conn.commit()

                            logger.info(f"Updated schedule for group {group}")
                            result[group] = new_data["schedule"]
                        else:
                            logger.info(f"No changes detected for group {group}")
                except Exception as e:
                    logger.exception(f"Error processing group {group}: {e}")

        except Exception as e:
            logger.exception(f"Error fetching group list: {e}")
            return {}

    return result


async def schedule_update_task():
    """
    Планировщик периодических обновлений расписания каждые 90 минут.
    Запускается как фоновая задача при старте приложения.
    """
    while True:
        try:
            logger.info("Starting scheduled schedule update")
            await check_schedule_update()
            logger.info("Scheduled schedule update completed")
        except Exception as e:
            logger.exception(f"Error during scheduled schedule update: {e}")

        # Ожидание 90 минут (5400 секунд) перед следующим запуском
        await asyncio.sleep(90 * 60)