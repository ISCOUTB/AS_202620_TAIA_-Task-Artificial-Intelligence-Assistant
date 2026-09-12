"""Reminder schedule value object."""

from pydantic import BaseModel, Field

from .reminder import Reminder


class ReminderSchedule(BaseModel):
    """Collection of reminders for a calendar month."""

    schedule: list[Reminder]
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1)
