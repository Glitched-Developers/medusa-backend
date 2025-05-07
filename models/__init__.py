from typing import Optional
from pydantic import BaseModel
from api import WeekActions

class WeekPayload(BaseModel):
    """
    Represents the payload for week-related actions.

    Attributes:
        week (Optional[int]): The week number. Defaults to None.
        action (WeekActions): The action to be performed for the week.
    """
    week: Optional[int] = None
    action: WeekActions

class WeekResponse(BaseModel):
    """
    Represents the response for week-related actions.

    Attributes:
        week (str): The week information as a string.
    """
    week: str

class SchedulePayload(BaseModel):
    """
    Represents the payload for fetching a schedule.

    Attributes:
        week (Optional[int]): The week number. Defaults to None.
        group (int): The group ID for which the schedule is requested.
    """
    week: Optional[int] = None
    group: int

class TodaySchedulePayload(BaseModel):
    """
    Represents the payload for fetching a schedule.

    Attributes:
        group (int): The group ID for which the schedule is requested.
    """
    group: int

class ScheduleResponse(BaseModel):
    """
    Represents the response containing the schedule.

    Attributes:
        schedule (dict): The schedule data as a dictionary.
    """
    schedule: dict
