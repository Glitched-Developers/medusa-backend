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

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AuditoriumItem(BaseModel):
    """One room from the BSU auditorium directory."""

    id: str = Field(..., description="BSU auditorium id")
    name: str = Field(..., description="Room name as published by BSU")
    token: str = Field(
        ...,
        description="Normalized room token, e.g. 6-7_12",
        json_schema_extra={"examples": ["6-7_12"]},
    )


class AuditoriumListResponse(BaseModel):
    """The stored id-to-name map."""

    auditoriums: List[AuditoriumItem]


class TeacherIdResponse(BaseModel):
    """Response model for teacher id lookup."""

    teacher_id: int = Field(
        ...,
        description="BSU teacher id",
        json_schema_extra={"examples": [128972]},
    )


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
        json_schema_extra={"examples": ["15"]},
    )


class SubgroupData(BaseModel):
    """Subgroup-specific lesson data."""

    discipline: str = Field(..., description="Subject name")
    teacher: str = Field(..., description="Instructor name")
    auditory: str = Field(..., description="Room number or location")
    online: bool = Field(..., description="Whether lesson is online")
    subgroup: int = Field(
        ..., ge=0, le=2, description="Subgroup number (0=all, 1 or 2=specific)"
    )


class LessonData(BaseModel):
    """Individual lesson entry in a day's schedule."""

    number: int = Field(..., ge=1, le=7, description="Lesson number in the day (1-7)")
    time: str = Field(
        ...,
        pattern=r"^\d{2}:\d{2}-\d{2}:\d{2}$",
        description="Time range (HH:MM-HH:MM)",
    )
    type: str = Field(..., description="Lesson type (lecture, lab, practice)")

    # Optional subgroup-specific fields
    subgroup_0: Optional[SubgroupData] = Field(
        None, description="All-subgroup lesson data"
    )
    subgroup_1: Optional[SubgroupData] = Field(
        None, description="Subgroup 1 specific data"
    )
    subgroup_2: Optional[SubgroupData] = Field(
        None, description="Subgroup 2 specific data"
    )

    @field_validator("number")
    @classmethod
    def validate_lesson_number(cls, v: int) -> int:
        """Ensure lesson number is within valid range."""
        if not 1 <= v <= 7:
            raise ValueError("Lesson number must be between 1 and 7")
        return v

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Ensure time follows HH:MM-HH:MM format."""
        import re

        if not re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}$", v):
            raise ValueError("Time must follow HH:MM-HH:MM format")
        return v


class ScheduleMetadata(BaseModel):
    """Schedule metadata containing timestamp information."""

    timestamp: str = Field(
        ..., description="ISO format timestamp when schedule was fetched"
    )


class ParsedSchedule(BaseModel):
    """Complete parsed schedule structure with validation.

    This model validates the internal structure returned by parse_schedule()
    before it's saved to the database or returned via API.
    """

    metadata: ScheduleMetadata = Field(..., description="Schedule metadata")
    schedule: Dict[str, List[LessonData]] = Field(
        ...,
        description="Schedule organized by weekday, each containing list of lessons",
    )

    @field_validator("schedule")
    @classmethod
    def validate_weekdays(
        cls, v: Dict[str, List[LessonData]]
    ) -> Dict[str, List[LessonData]]:
        """Ensure schedule keys are valid weekday names."""
        valid_days = {
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
        }
        invalid_days = set(v.keys()) - valid_days
        if invalid_days:
            raise ValueError(f"Invalid weekday names: {invalid_days}")
        return v


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
        json_schema_extra={
            "examples": [
                {
                    "days": {
                        "monday": [
                            {
                                "time": "08:30-10:05",
                                "subject": "Mathematics",
                                "room": "101",
                                "instructor": "Dr. Smith",
                            }
                        ]
                    },
                    "group": 12345,
                    "week": 15,
                }
            ]
        },
    )
