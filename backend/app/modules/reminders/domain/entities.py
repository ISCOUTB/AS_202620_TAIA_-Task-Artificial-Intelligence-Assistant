"""Domain entities for the reminders module.

Rules (same as the `ai` module):
- Only data models and shape validation (Pydantic).
- No side effects: no `datetime.now()`, no network calls, no
  Telegram/DB access here.
- Orchestration (creating notifications, marking as completed, etc.)
  lives in `application/use_cases`.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Reminder(BaseModel):
    """Reminder linked to an academic task."""

    id: int
    user_id: UUID
    message: str
    scheduled_at: datetime
    is_completed: bool = False
    task_id: int  # reference to Task.id in the academic module


class Notification(BaseModel):
    """Notification derived from a Reminder."""

    reminder_id: int
    message: str
    read_status: bool = False
    date_send: datetime


class ReminderSchedule(BaseModel):
    """Agenda of reminders for a given month/year."""

    schedule: list[Reminder]
    month: int
    year: int
