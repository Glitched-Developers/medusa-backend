from typing import Optional

from pydantic import BaseModel

from api import WeekActions


class WeekPayload(BaseModel):
    week: Optional[int] = None
    action: WeekActions

class WeekResponse(BaseModel):
    week: str

class SchedulePayload(BaseModel):
    week: Optional[int] = None
    group: int

class ScheduleResponse(BaseModel):
    schedule: dict