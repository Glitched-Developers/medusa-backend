"""
API Routes Module

This module defines the REST API endpoints for the Medusa Backend application.
It provides endpoints for fetching week calculations and BSU class schedules.

Available endpoints:
- GET /weeks: Get week number calculations
- GET /groups/{group_id}/schedules/current: Get current schedule for a group
- GET /groups/{group_id}/schedules: Get schedule for a specific group and week
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

import tasks
from api import fetch_week, fetch_schedule, WeekActions
from models import WeekResponse, ScheduleResponse

# Initialize router with tags for API documentation
router = APIRouter(
    tags=["schedules"],
    responses={
        503: {"description": "Service unavailable - connection error"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/weeks", 
    response_model=WeekResponse,
    summary="Get week number",
    description="Calculate week number based on action (current/next/previous week)"
)
async def get_weeks(
    action: WeekActions = Query(
        WeekActions.THIS_WEEK, 
        description="Week action to perform (this_week, next_week, last_week)"
    ),
    week: Optional[int] = Query(
        None, 
        description="Base week number for calculations (optional)"
    )
) -> WeekResponse:
    """
    Get the week number based on the specified action and optional base week.

    This endpoint calculates academic week numbers for BSU schedule system.
    It can return the current week, next week, or previous week number.

    Args:
        action: Week action to perform (this_week, next_week, last_week)
        week: Base week number for relative calculations (optional)

    Returns:
        WeekResponse: JSON response containing the calculated week number

    Raises:
        HTTPException: 
            - 503: Service unavailable due to connection errors
            - 500: Internal server error for unexpected issues

    Example:
        GET /weeks?action=this_week -> {"week": "15"}
        GET /weeks?action=next_week&week=10 -> {"week": "11"}
    """
    try:
        week_number = await fetch_week(action=action, week=week or 0)
        return WeekResponse(week=str(week_number))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/groups/{group_id}/schedules/current", 
    response_model=ScheduleResponse,
    summary="Get current schedule",
    description="Fetch the current week's schedule for a specific group"
)
async def get_current_schedule(
    group_id: int = Query(..., description="BSU group ID", example=12345)
) -> ScheduleResponse:
    """
    Get current schedule for a specific BSU group.

    This endpoint fetches the schedule for the current academic week.
    It automatically determines the current week and returns the corresponding schedule.
    The schedule data is automatically updated via background tasks.

    Args:
        group_id: The BSU group ID for which the schedule is requested

    Returns:
        ScheduleResponse: JSON response containing the current schedule data

    Raises:
        HTTPException: 
            - 503: Service unavailable due to connection errors
            - 500: Internal server error for unexpected issues

    Example:
        GET /groups/12345/schedules/current
    """
    try:
        schedule = await tasks.check_schedule_update(group_id)
        return ScheduleResponse(schedule=schedule)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
@router.get(
    "/groups/{group_id}/schedules", 
    response_model=ScheduleResponse,
    summary="Get schedule by week",
    description="Fetch schedule for a specific group and week number"
)
async def get_schedules(
    group_id: int = Query(..., description="BSU group ID", example=12345),
    week: Optional[int] = Query(
        None, 
        description="Academic week number (defaults to current week)", 
        example=15
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
        schedule = await fetch_schedule(group=group_id, week=week)
        return ScheduleResponse(schedule=schedule)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


