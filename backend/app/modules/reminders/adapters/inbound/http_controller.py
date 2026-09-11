"""HTTP inbound adapter. Depends only on the inbound ports, never on
the concrete use case classes.

Adjust the dependency injection (Depends) to however you resolve it
in your project (DI container, factory, etc.).
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.modules.reminders.application.ports.inbound.reminder_ports import (
    CreateReminderPort,
    DeleteReminderPort,
    EditReminderPort,
    GetReminderPort,
    ListRemindersPort,
    MarkReminderCompletedPort,
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


class CreateReminderRequest(BaseModel):
    user_id: UUID
    message: str
    scheduled_at: datetime
    task_id: int


class EditReminderRequest(BaseModel):
    message: str | None = None
    scheduled_at: datetime | None = None


@router.post("/")
def create_reminder(
    payload: CreateReminderRequest,
    use_case: CreateReminderPort = Depends(),
):
    return use_case.execute(
        user_id=payload.user_id,
        message=payload.message,
        scheduled_at=payload.scheduled_at,
        task_id=payload.task_id,
    )


@router.get("/")
def list_reminders(
    user_id: UUID,
    use_case: ListRemindersPort = Depends(),
):
    return use_case.execute(user_id)


@router.get("/{reminder_id}")
def get_reminder(
    reminder_id: int,
    user_id: UUID,
    use_case: GetReminderPort = Depends(),
):
    return use_case.execute(reminder_id, user_id)


@router.patch("/{reminder_id}")
def edit_reminder(
    reminder_id: int,
    user_id: UUID,
    payload: EditReminderRequest,
    use_case: EditReminderPort = Depends(),
):
    return use_case.execute(
        reminder_id, user_id, payload.message, payload.scheduled_at
    )


@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    user_id: UUID,
    use_case: DeleteReminderPort = Depends(),
):
    use_case.execute(reminder_id, user_id)
    return {"deleted": True}


@router.post("/{reminder_id}/complete")
def mark_reminder_completed(
    reminder_id: int,
    user_id: UUID,
    use_case: MarkReminderCompletedPort = Depends(),
):
    return use_case.execute(reminder_id, user_id)
