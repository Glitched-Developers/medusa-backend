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

import uvicorn

from logger import setup_logging
from fastapi import FastAPI

from database import init_database
from routes import router
from tasks import schedule_update_task

# Initialize the logger
logger = setup_logging("INFO")

# FastAPI application instance with metadata
app = FastAPI(
    title="Medusa Backend API",
    description="RESTful API for BSU class schedules management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.include_router(router)

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
    # Initialize the database
    logger.info("Initializing the database...")
    await init_database()

    # Start background task for automated schedule updates
    logger.info("Starting the scheduled update task...")
    asyncio.create_task(schedule_update_task())

    # Configure and start the web server
    logger.info("Starting the server...")
    logger.info(f"Server will run on http://localhost:8080")
    
    config = uvicorn.Config(
        "main:app", 
        host="0.0.0.0", 
        port=8080,
        log_level="info"
    )
    server = uvicorn.Server(config)

    await server.serve()

if __name__ == "__main__":
    """Entry point when script is run directly."""
    asyncio.run(main())