"""Notification domain entity."""

from datetime import datetime

from pydantic import BaseModel


class Notification(BaseModel):
    """Notification generated from a reminder."""

    reminder_id: int
    message: str
    read_status: bool = False
    date_send: datetime
