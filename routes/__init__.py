from fastapi import APIRouter, HTTPException
from api import fetch_week, fetch_schedule
from models import WeekPayload, WeekResponse, SchedulePayload, ScheduleResponse

router = APIRouter()


@router.post("/week", response_model=WeekResponse)
async def get_week_endpoint(payload: WeekPayload) -> WeekResponse:
    """
    Endpoint to get the week number based on the action and optional base week.

    Args:
        payload: The request payload with action and optional week

    Returns:
        WeekResponse containing the calculated week number

    Raises:
        HTTPException: If there's an error fetching the week data
    """
    try:
        week_number = await fetch_week(action=payload.action, week=payload.week or 0)
        return WeekResponse(week=str(week_number))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/schedule", response_model=ScheduleResponse)
async def get_schedule_endpoint(payload: SchedulePayload):
    """
    Endpoint to get the schedule based on the action and optional base week.

    Args:
        payload: The request payload with action and optional week

    Returns:
        ScheduleResponse containing the calculated schedule

    Raises:
        HTTPException: If there's an error fetching the schedule data
    """
    try:
        schedule = await fetch_schedule(group=payload.group, week=payload.week)
        return ScheduleResponse(schedule=schedule)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


