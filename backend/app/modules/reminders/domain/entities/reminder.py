"""Reminder domain entity."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Reminder(BaseModel):
    """Reminder linked to an academic task."""

    model_config = ConfigDict(validate_assignment=True)

    id: int
    user_id: UUID
    message: str = Field(min_length=1)
    scheduled_at: datetime
    is_completed: bool = False
    task_id: UUID

    def mark_completed(self) -> "Reminder":
        """Return a completed copy of this reminder."""
        return self.model_copy(update={"is_completed": True})
