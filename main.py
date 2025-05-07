import asyncio
import uvicorn

from logger import setup_logging
from fastapi import FastAPI

from database import init_database
from routes import router
from tasks import schedule_update_task

# Настройка логирования
logger = setup_logging("INFO")

app = FastAPI()
app.include_router(router)

async def main():
    """uvicorn server entry point."""

    # Initialize the database
    logger.info("Initializing the database...")
    await init_database()

    logger.info("Starting the scheduled update task...")
    asyncio.create_task(schedule_update_task())

    logger.info("Starting the server...")
    config = uvicorn.Config("main:app", host="localhost", port=5000, log_level="info")
    server = uvicorn.Server(config)

    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())