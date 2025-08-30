"""
Utilities Module

This module provides utility functions for the Medusa Backend application,
including validation functions and helper utilities used across the codebase.

Key Functions:
- week_validator: Validates BSU week codes in DDMMYYYYDDMMYYYY format
- Date range validation and format checking
- Input sanitization and error handling
"""

from fastapi import HTTPException
from datetime import datetime
import calendar


def week_validator(week) -> bool:
    """
    Validate BSU week code format and date ranges.
    
    BSU uses a 16-digit week code format: DDMMYYYYDDMMYYYY
    This represents a date range from start date to end date.
    
    Format breakdown:
    - DD: Day (01-31)
    - MM: Month (01-12) 
    - YYYY: Year (4 digits)
    - DDMMYYYY: End date in same format
    
    The function validates:
    1. Correct 16-digit length
    2. Valid date components (day, month, year)
    3. Proper date ranges for each month (accounting for leap years)
    4. End date is after start date
    
    Args:
        week (int): BSU week code as integer (16 digits)
        
    Returns:
        bool: True if week code is valid
        
    Raises:
        HTTPException: 400 status with detailed error message if validation fails
        
    Examples:
        >>> week_validator(1012025080120025)  # Jan 1-8, 2025
        True
        >>> week_validator(123456789)  # Too short
        HTTPException: Invalid week code, must be exactly 16 digits long
        >>> week_validator(3113202501012025)  # Invalid date (Dec 31 to Jan 1)
        HTTPException: Invalid start date: day must be between 1 and 30 for month 13
    """
    week_str = str(week)

    # Validate length requirement (15-16 digits allowed)
    if len(week_str) < 15 or len(week_str) > 16:
        raise HTTPException(
            status_code=400, 
            detail="Invalid week code, must be 15-16 digits long"
        )
    
    # Pad with leading zero if 15 digits
    if len(week_str) == 15:
        week_str = "0" + week_str

    try:
        # Parse date components from week code
        # Format: DDMMYYYYDDMMYYYY
        start_day = int(week_str[0:2])      # DD
        start_month = int(week_str[2:4])    # MM  
        start_year = int(week_str[4:8])     # YYYY
        
        end_day = int(week_str[8:10])       # DD
        end_month = int(week_str[10:12])    # MM
        end_year = int(week_str[12:16])     # YYYY
        
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid week code format, must contain only digits"
        )

    # Validate month ranges (1-12)
    if not (1 <= start_month <= 12):
        raise HTTPException(
            status_code=400, 
            detail="Invalid start date: month must be between 1 and 12"
        )

    if not (1 <= end_month <= 12):
        raise HTTPException(
            status_code=400, 
            detail="Invalid end date: month must be between 1 and 12"
        )

    # Get maximum days for each month (handles leap years)
    try:
        start_max_days = calendar.monthrange(start_year, start_month)[1]
        end_max_days = calendar.monthrange(end_year, end_month)[1]
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid year or month in the week code"
        )

    # Validate day ranges based on month/year
    if not (1 <= start_day <= start_max_days):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid start date: day must be between 1 and {start_max_days} for month {start_month}"
        )

    if not (1 <= end_day <= end_max_days):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid end date: day must be between 1 and {end_max_days} for month {end_month}"
        )

    # Create datetime objects for comprehensive date validation
    try:
        start_date = datetime(start_year, start_month, start_day)
        end_date = datetime(end_year, end_month, end_day)

        # Ensure end date is after start date
        if end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="Invalid week code: end date must be after start date"
            )

        # Note: BSU week periods may vary in length, so we don't enforce exactly 7 days
        # This allows for flexibility in academic calendar scheduling

    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date in the week code"
        )

    # All validations passed
    return True
