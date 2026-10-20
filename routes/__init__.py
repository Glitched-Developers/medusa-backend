"""
API Routes Module

This module defines the REST API endpoints for the Medusa Backend application.
It provides endpoints for fetching week calculations and BSU class schedules.

Available endpoints:
- GET /: Redirect to API documentation
- GET /stats: Get server status as JSON API
- GET /weeks: Get week number calculations
- GET /groups/{group_id}/schedules: Get schedule for a specific group and week
"""

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import RedirectResponse
from typing import Optional
import datetime
import traceback
from loguru import logger

import tasks
from api import fetch_week, fetch_schedule, WeekActions
from database import save_schedule
from models import WeekResponse, ScheduleResponse
from utils.version import get_version, get_git_commit, get_git_branch

# Initialize router with tags for API documentation
router = APIRouter(
    tags=["schedules"],
    responses={
        503: {"description": "Service unavailable - connection error"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/",
    summary="Redirect to docs",
    description="Redirect to the API documentation"
)
async def redirect_to_docs():
    """
    Redirect to the API documentation.
    
    Returns:
        RedirectResponse: Redirect to API docs
    """
    return RedirectResponse(url="/docs", status_code=302)


@router.get(
    "/stats",
    summary="Server status API",
    description="Get server status and basic information as JSON"
)
async def get_server_stats():
    """
    Get server status with basic information.
    
    Returns server health status, current time, and API information as JSON.
    Now includes Git-based version information with commit hash and branch.
    
    Returns:
        dict: Server status information including:
            - status: Server health status
            - timestamp: Current server time
            - service_info: API metadata
            - git_info: Git version, commit, and branch information
    
    Example:
        GET /stats -> {"status": "OK", "timestamp": "2024-01-15T10:30:00Z", "version": "v1.0.0+abc1234", ...}
    """
    # Get Git information
    version = get_version()
    commit = get_git_commit()
    branch = get_git_branch()
    
    response = {
        "status": "OK",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "service": "Medusa Backend API",
        "version": version,
        "description": "RESTful API for BSU class schedules management",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "weeks": "/weeks",
            "schedules": "/groups/{group_id}/schedules"
        }
    }
    
    # Add Git information if available
    git_info = {}
    if commit:
        git_info["commit"] = commit
    if branch:
        git_info["branch"] = branch
    
    if git_info:
        response["git"] = git_info
    
    return response


@router.get(
    "/weeks", 
    response_model=WeekResponse,
    summary="Get week number",
    description="Calculate week number based on action (current/next/previous week)"
)
async def get_weeks(
    action: str = Query(
        "this", 
        description="Week action to perform (this, next, last)"
    ),
    week: Optional[str] = Query(
        None, 
        description="Base week number for calculations (optional)"
    )
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
            "last": WeekActions.LAST_WEEK
        }
        
        week_action = action_mapping.get(action, WeekActions.THIS_WEEK)
        week_number = await fetch_week(action=week_action, week=week or "0")
        logger.debug(f"Calculated week: {week_number}")
        return WeekResponse(week=str(week_number))
    except ConnectionError as e:
        logger.error(f"Connection error in get_weeks: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_weeks: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/groups/{group_id}/schedules/current", 
    response_model=ScheduleResponse,
    summary="Get current schedule",
    description="Fetch the current week's schedule for a specific group"
)
@router.get(
    "/groups/{group_id}/schedules", 
    response_model=ScheduleResponse,
    summary="Get schedule by week",
    description="Fetch schedule for a specific group and week number"
)
async def get_schedules(
    group_id: int = Path(..., description="BSU group ID", examples=[12345]),
    week: Optional[str] = Query(
        None, 
        description="Academic week number (defaults to current week)", 
        examples=["0109202507092025"]
    )
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
        logger.error(f"Connection error in get_schedules for group {group_id}: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_schedules for group {group_id}: {type(e).__name__}: {e}\n{traceback.format_exc()}")
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
) -> ScheduleResponse:
    try:
        schedule = await fetch_schedule(group=group_id, week=week)
        await save_schedule(group_id, schedule)
        return ScheduleResponse(schedule=schedule)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Failed to refresh schedule for group %s", group_id)
        raise HTTPException(status_code=500, detail=str(e))
