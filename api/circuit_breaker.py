"""
Circuit breaker для защиты от каскадных ошибок при недоступности BSU API.

Использует pybreaker для реализации circuit breaker pattern с конфигурируемыми
параметрами: fail_max (количество ошибок до открытия), timeout (время recovery),
и excluded exceptions (ошибки, не влияющие на открытие breaker).
"""

import os
from loguru import logger
from pybreaker import CircuitBreaker, CircuitBreakerError
import httpx


# Конфигурация circuit breaker из переменных окружения
BREAKER_FAIL_MAX = int(os.getenv("CIRCUIT_BREAKER_FAIL_MAX", "5"))
BREAKER_TIMEOUT_SECONDS = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT_SECONDS", "60"))

# Создание глобального circuit breaker для BSU upstream
bsu_breaker = CircuitBreaker(
    fail_max=BREAKER_FAIL_MAX,
    reset_timeout=BREAKER_TIMEOUT_SECONDS,
    exclude=[
        httpx.HTTPStatusError,  # 4xx ошибки не должны открывать breaker
    ],
    name="bsu_upstream",
)


def is_breaker_open() -> bool:
    """
    Проверяет, открыт ли circuit breaker в данный момент.

    Returns:
        True если breaker открыт (upstream недоступен), False иначе
    """
    return bsu_breaker.current_state == "open"


def get_breaker_state() -> dict:
    """
    Возвращает текущее состояние circuit breaker для мониторинга.

    Returns:
        dict: Словарь с полями state, fail_counter, last_failure_time
    """
    return {
        "state": bsu_breaker.current_state,
        "fail_counter": bsu_breaker.fail_counter,
        "last_failure": (
            bsu_breaker.last_failure_time.isoformat()
            if bsu_breaker.last_failure_time
            else None
        ),
    }
