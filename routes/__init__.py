"""
API Routes Module

This module defines the REST API endpoints for the Medusa Backend application.
It provides endpoints for fetching week calculations and BSU class schedules.

Available endpoints:
- GET /: Redirect to API documentation
- GET /weeks: Get week number calculations
- GET /groups/{group_id}/schedules: Get schedule for a specific group and week
"""

import os
import traceback
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text

from api import WeekActions, fetch_schedule, fetch_week
from api.circuit_breaker import get_breaker_state
from cache import schedule_cache
from database import engine, save_schedule
from models import ScheduleResponse, WeekResponse
from observability.metrics import api_requests
from routes.mail import router as mail_router

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize router with tags for API documentation
router = APIRouter(
    tags=["schedules"],
    responses={
        503: {"description": "Service unavailable - connection error"},
        500: {"description": "Internal server error"},
        429: {"description": "Too many requests - rate limit exceeded"},
    },
)
router.include_router(mail_router)


@router.get(
    "/health",
    summary="Check service health",
    description="Check database, Redis, circuit breaker, and background updater readiness.",
    tags=["health"],
)
async def health_check(request: Request):
    checks = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    try:
        await schedule_cache._get_client().ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
    checks["circuit_breaker"] = get_breaker_state()
    updater = getattr(request.app.state, "updater", None)
    checks["background_updater"] = (
        "ok" if updater is None or not updater.done() else "stopped"
    )
    healthy = checks["database"] == "ok" and checks["redis"] == "ok"
    return {"status": "ok" if healthy else "degraded", "checks": checks}


@router.get(
    "/", summary="Redirect to docs", description="Redirect to the API documentation"
)
async def redirect_to_docs():
    """
    Redirect to the API documentation.

    Returns:
        RedirectResponse: Redirect to API docs
    """
    return RedirectResponse(url="/docs", status_code=302)


@router.get(
    "/weeks",
    response_model=WeekResponse,
    summary="Get week number",
    description="Calculate week number based on action (current/next/previous week)",
)
@limiter.limit("60/minute")
async def get_weeks(
    request: Request,
    action: str = Query(
        "this", description="Week action to perform (this, next, last)"
    ),
    week: Optional[str] = Query(
        None, description="Base week number for calculations (optional)"
    ),
) -> WeekResponse:
    """
    Get the week number based on the specified action and optional base week.

    This endpoint calculates academic week numbers for BSU schedule system.
    It can return the current week, next week, or previous week number.

    Args:
        action: Week action to perform (this, next, last)
        week: Base week number for relative calculations (optional)

    Returns:
        WeekResponse: JSON response containing the calculated week number

    Raises:
        HTTPException:
            - 503: Service unavailable due to connection errors
            - 500: Internal server error for unexpected issues

    Example:
        GET /weeks?action=this -> {"week": "15"}
        GET /weeks?action=next&week=2508202531082025 -> {"week": "2608202531082025"}
    """
    try:
        logger.info(f"Week calculation request: action={action}, week={week}")
        # Convert string action to enum
        action_mapping = {
            "this": WeekActions.THIS_WEEK,
            "next": WeekActions.NEXT_WEEK,
            "last": WeekActions.LAST_WEEK,
        }

        week_action = action_mapping.get(action, WeekActions.THIS_WEEK)
        week_number = await fetch_week(action=week_action, week=week or "0")
        logger.debug(f"Calculated week: {week_number}")
        return WeekResponse(week=str(week_number))
    except ConnectionError as e:
        logger.error(
            f"Connection error in get_weeks: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error in get_weeks: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get(
    "/groups/{group_id}/schedules/current",
    response_model=ScheduleResponse,
    summary="Get current schedule",
    description="Fetch the current week's schedule for a specific group",
)
@router.get(
    "/groups/{group_id}/schedules",
    response_model=ScheduleResponse,
    summary="Get schedule by week",
    description="Fetch schedule for a specific group and week number",
)
@limiter.limit("60/minute")
async def get_schedules(
    request: Request,
    group_id: int = Path(..., description="BSU group ID", examples=[12345]),
    week: Optional[str] = Query(
        None,
        description="Academic week number (defaults to current week)",
        examples=["0109202507092025"],
    ),
) -> ScheduleResponse:
    """
    Get schedule for a specific BSU group and academic week.

    This endpoint allows fetching schedules for any specific week number.
    If no week is specified, it defaults to the current academic week.
    The schedule data includes class times, subjects, rooms, and instructors.

    Args:
        group_id: The BSU group ID for which the schedule is requested
        week: Academic week number (optional, defaults to current week)

    Returns:
        ScheduleResponse: JSON response containing the schedule data for the specified week

    Raises:
        HTTPException:
            - 503: Service unavailable due to connection errors
            - 500: Internal server error for unexpected issues

    Example:
        GET /groups/12345/schedules?week=15
        GET /groups/12345/schedules  # Uses current week
    """
    try:
        logger.info(f"Schedule request: group_id={group_id}, week={week}")
        schedule = await fetch_schedule(group=group_id, week=week)
        await save_schedule(group_id, schedule)
        logger.info(f"Successfully fetched schedule for group {group_id}")
        return ScheduleResponse(schedule=schedule)
    except ConnectionError as e:
        logger.error(
            f"Connection error in get_schedules for group {group_id}: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error in get_schedules for group {group_id}: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post(
    "/groups/{group_id}/schedules/refresh",
    response_model=ScheduleResponse,
    summary="Refresh schedule",
    description="Fetch the latest schedule and persist it for background updates",
)
async def refresh_schedule(
    group_id: int = Path(..., description="BSU group ID", examples=[12345]),
    week: Optional[str] = Query(None, description="Academic week number"),
    authorization: Optional[str] = Header(None),
) -> ScheduleResponse:
    """Refresh and persist a group's schedule using the protected admin endpoint.

    The request requires ``ADMIN_API_TOKEN`` and is rate-limited per group.
    """
    admin_token = os.getenv("ADMIN_API_TOKEN")
    # Sanitize Authorization header in logs
    masked_auth = (
        "Bearer ***" if authorization and authorization.startswith("Bearer ") else None
    )

    if not admin_token or authorization != f"Bearer {admin_token}":
        logger.warning(
            f"Unauthorized admin refresh attempt for group {group_id}, auth: {masked_auth}"
        )
        raise HTTPException(status_code=401, detail="Admin API token required")
    rate_limit = int(os.getenv("ADMIN_REFRESH_RATE_LIMIT", "5"))
    rate_window = int(os.getenv("ADMIN_REFRESH_RATE_WINDOW_SECONDS", "60"))
    allowed = await schedule_cache.allow_request(
        f"medusa:admin-refresh:{group_id}", rate_limit, rate_window
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Refresh rate limit exceeded")
    lock_token = await schedule_cache.acquire_lock(f"admin-refresh:{group_id}", ttl=300)
    if not lock_token:
        raise HTTPException(status_code=409, detail="A refresh is already in progress")
    try:
        schedule = await fetch_schedule(group=group_id, week=week)
        await save_schedule(group_id, schedule)
        api_requests.labels("POST", "/groups/{group_id}/schedules/refresh", "200").inc()
        return ScheduleResponse(schedule=schedule)
    except ConnectionError as e:
        api_requests.labels("POST", "/groups/{group_id}/schedules/refresh", "503").inc()
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        api_requests.labels("POST", "/groups/{group_id}/schedules/refresh", "500").inc()
        logger.exception("Failed to refresh schedule for group %s", group_id)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await schedule_cache.release_lock(f"admin-refresh:{group_id}", lock_token)
