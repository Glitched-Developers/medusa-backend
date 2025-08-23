"""
Data Models Module

This module defines Pydantic data models for API request/response validation
and serialization in the Medusa Backend application. These models ensure
type safety and automatic JSON schema generation for FastAPI endpoints.

The models provide:
- Request/response validation
- Automatic OpenAPI documentation
- Type hints for IDE support
- JSON serialization/deserialization
"""

from pydantic import BaseModel, Field
from typing import Dict, Any


class WeekResponse(BaseModel):
    """
    Response model for week calculation endpoints.
    
    This model represents the response returned by week-related API endpoints
    that calculate academic week numbers based on various actions (current, next, previous).
    
    Attributes:
        week (str): The calculated academic week number as a string.
                   Formatted as a string to maintain consistency with BSU's system.
    
    Example:
        {
            "week": "15"
        }
    """
    week: str = Field(
        ..., 
        description="Academic week number as string",
        example="15"
    )


class ScheduleResponse(BaseModel):
    """
    Response model for schedule data endpoints.
    
    This model represents the response returned by schedule-related API endpoints
    that fetch BSU class schedules. The schedule data contains detailed information
    about classes, times, rooms, and instructors.
    
    Attributes:
        schedule (Dict[str, Any]): Complete schedule data structure containing
                                  class information, times, rooms, instructors,
                                  and other schedule metadata.
    
    Example:
        {
            "schedule": {
                "days": {
                    "monday": [
                        {
                            "time": "08:30-10:05",
                            "subject": "Mathematics",
                            "room": "101",
                            "instructor": "Dr. Smith"
                        }
                    ]
                },
                "group": 12345,
                "week": 15
            }
        }
    """
    schedule: Dict[str, Any] = Field(
        ..., 
        description="Complete schedule data with class information",
        example={
            "days": {
                "monday": [
                    {
                        "time": "08:30-10:05",
                        "subject": "Mathematics",
                        "room": "101",
                        "instructor": "Dr. Smith"
                    }
                ]
            },
            "group": 12345,
            "week": 15
        }
    )
