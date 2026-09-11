from pydantic import BaseModel
from entities.reminder import Reminder


class ReminderSchedule(BaseModel):
    schedule: list[Reminder]
    month: int 
    year: int