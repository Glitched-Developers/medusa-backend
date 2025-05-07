import sys
import logging
from loguru import logger


# Перехватчик стандартных логов Python для перенаправления в loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Получаем соответствующий уровень Loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Находим вызывающий кадр, откуда пришло сообщение
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_level="INFO"):
    """
    Настройка логирования в приложении с перехватом стандартных логов

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  По умолчанию: INFO

    Returns:
        Настроенный объект logger
    """
    # Настройка loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": log_level,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
            }
        ]
    )

    # Получаем числовой уровень логирования для стандартного логгера
    logging_level = getattr(logging, log_level)

    # Перенаправление стандартных логов в loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=logging_level)

    # Перехват логов uvicorn и fastapi
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False
        _logger.setLevel(logging_level)

    return logger