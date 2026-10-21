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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import init_database
from routes import router
from tasks import schedule_update_task
from observability.metrics import metrics_app
from utils.version import get_version

# Initialize the logger
logger = setup_logging("INFO")

# Initialize rate limiter for public endpoints
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


# FastAPI application instance with metadata
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize resources on startup and stop background work on shutdown."""
    # Validate required environment variables
    admin_token = os.getenv("ADMIN_API_TOKEN")
    if not admin_token:
        logger.warning(
            "ADMIN_API_TOKEN is not set. Admin refresh endpoint will be unavailable."
        )
    
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

# Register rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware to allow requests from dashboard
# CORS origins are configurable via CORS_ALLOWED_ORIGINS env var (comma-separated)
# Default: localhost development ports
cors_origins_str = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000",
)
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
