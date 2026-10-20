"""
Logging Module

This module provides centralized logging configuration for the Medusa Backend application.
It uses loguru for enhanced logging capabilities and intercepts standard Python logging
to redirect all log messages through loguru for consistent formatting.

Features:
- Colored console output with timestamps
- Intercepts uvicorn and FastAPI logs
- Configurable log levels
- Consistent formatting across all components
"""

import sys
import logging
from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Custom logging handler to intercept standard Python logging and redirect to loguru.

    This handler captures log messages from Python's standard logging module
    and redirects them to loguru for consistent formatting and output.
    """

    def emit(self, record):
        """
        Process a log record and redirect it to loguru.

        Args:
            record: Python logging LogRecord instance

        The original exception information is preserved when forwarding the
        record to Loguru.
        """
        # Map Python logging level to loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the calling frame for accurate source information
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Log the message through loguru with proper context
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_level="INFO"):
    """
    Configure application logging with loguru and intercept standard Python logs.

    This function sets up centralized logging for the entire application:
    - Configures loguru with colored console output
    - Intercepts standard Python logging messages
    - Redirects uvicorn and FastAPI logs through loguru
    - Provides consistent formatting across all components

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                        Defaults to "INFO"

    Returns:
        loguru.Logger: Configured logger instance ready for use

    Example:
        >>> logger = setup_logging("DEBUG")
        >>> logger.info("Application started")
    """
    # Configure loguru with colored console output
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": log_level,
                "format": (
                    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                    "<level>{message}</level>"
                ),
            }
        ]
    )

    # Convert string level to logging module level
    logging_level = getattr(logging, log_level.upper())

    # Redirect standard Python logging to loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=logging_level)

    # Intercept and redirect web framework logs
    for logger_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        web_logger = logging.getLogger(logger_name)
        web_logger.handlers = [InterceptHandler()]
        web_logger.propagate = False
        web_logger.setLevel(logging_level)

    return logger
