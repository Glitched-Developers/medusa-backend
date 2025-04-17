from fastapi import HTTPException

from fastapi import HTTPException
from datetime import datetime
import calendar


def week_validator(week: int):
    """
    Validates a week code in format DDMMYYYYDDMMYYYY.
    For example: 0101202508012025 means from 01.01.2025 to 08.01.2025.

    Args:
        week: Week code as integer

    Raises:
        HTTPException: If the week code is invalid
    """
    week_str = str(week)

    # Check length
    if len(week_str) != 16:
        raise HTTPException(status_code=400, detail="Invalid week code, must be exactly 16 digits long")

    try:
        # Extract date components
        start_day = int(week_str[0:2])
        start_month = int(week_str[2:4])
        start_year = int(week_str[4:8])

        end_day = int(week_str[8:10])
        end_month = int(week_str[10:12])
        end_year = int(week_str[12:16])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid week code format, must contain only digits")

    # Validate month ranges
    if start_month < 1 or start_month > 12:
        raise HTTPException(status_code=400, detail="Invalid start date: month must be between 1 and 12")

    if end_month < 1 or end_month > 12:
        raise HTTPException(status_code=400, detail="Invalid end date: month must be between 1 and 12")

    # Get max days for each month
    try:
        start_max_days = calendar.monthrange(start_year, start_month)[1]
        end_max_days = calendar.monthrange(end_year, end_month)[1]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid year or month in the week code")

    # Validate day ranges
    if start_day < 1 or start_day > start_max_days:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid start date: day must be between 1 and {start_max_days} for month {start_month}"
        )

    if end_day < 1 or end_day > end_max_days:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid end date: day must be between 1 and {end_max_days} for month {end_month}"
        )

    # Create datetime objects to validate dates and check if end date is after start date
    try:
        start_date = datetime(start_year, start_month, start_day)
        end_date = datetime(end_year, end_month, end_day)

        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="Invalid week code: end date must be after start date"
            )

        # Optional: check if the period is exactly one week (7 days)
        # days_diff = (end_date - start_date).days
        # if days_diff != 7:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Invalid week period: should be exactly 7 days, got {days_diff} days"
        #     )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date in the week code")

    # If everything passed, the week code is valid
    return True
