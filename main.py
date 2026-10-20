"""
Medusa Backend - BSU Schedule API Server

This module serves as the main entry point for the Medusa Backend application,
which provides a RESTful API for fetching and managing BSU (Belgorod State University)
class schedules.

The application includes:
- FastAPI web framework for REST API endpoints
- SQLite database for schedule persistence
- Automated background tasks for schedule updates
- Configurable port via environment variables
"""

import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn

from logger import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_database
from routes import router
from tasks import schedule_update_task
from observability.metrics import metrics_app
from utils.version import get_version

# Initialize the logger
logger = setup_logging("INFO")


# FastAPI application instance with metadata
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize resources on startup and stop background work on shutdown."""
    await init_database()
    updater = None
    if os.getenv("SCHEDULE_UPDATER_ENABLED", "true").lower() in {"1", "true", "yes"}:
        updater = asyncio.create_task(schedule_update_task())
    try:
        yield
    finally:
        if updater is not None:
            updater.cancel()
            await asyncio.gather(updater, return_exceptions=True)


app = FastAPI(
    title="Medusa Backend API",
    description="RESTful API for BSU class schedules management",
    version=get_version(),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware to allow requests from dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default development port
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",  # Alternative localhost and port
        "http://localhost:8080",  # Backend server itself
        "http://127.0.0.1:8080",  # Alternative backend URL
        "http://localhost:8000",  # Alternative backend port
        "http://127.0.0.1:8000",  # Alternative backend URL and port
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/metrics", metrics_app)


async def main():
    """
    Main application entry point.

    Initializes the database, starts background tasks, and runs the FastAPI server.
    The server listens on localhost with a configurable port (default: 8000).

    Environment Variables:
        PORT (int): Server port number (default: 8000)

    Raises:
        Exception: If database initialization or server startup fails
    """
    # Configure and start the web server
    logger.info("Starting the server...")
    logger.info("Server will run on http://localhost:8080")

    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        log_level="info",
    )
    server = uvicorn.Server(config)

    await server.serve()


if __name__ == "__main__":
    """Entry point when script is run directly."""
    asyncio.run(main())
