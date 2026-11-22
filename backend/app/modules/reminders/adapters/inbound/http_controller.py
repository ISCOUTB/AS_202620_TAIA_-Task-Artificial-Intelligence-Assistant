"""Adaptador HTTP de recordatorios (RF-REC-01, 03, 04 y 05)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.modules.reminders.application.errors import (
    ReminderNotFoundError,
    ReminderStateError,
    ReminderTaskNotFoundError,
)
from app.modules.reminders.application.ports.inbound.reminder_ports import (
    CreateReminderPort,
    DeleteReminderPort,
    EditReminderPort,
    GetReminderPort,
    ListRemindersPort,
)
from app.modules.reminders.domain.entities import Reminder, ReminderOrigin, ReminderStatus
from app.modules.reminders.domain.entities.reminder import MAX_MESSAGE_LENGTH
from app.shared.adapters.inbound.auth import CurrentUserId

router = APIRouter(prefix="/reminders", tags=["reminders"])

ScheduledAt = Annotated[
    datetime,
    Field(description="Momento del aviso. Sin zona horaria, se interpreta como hora de Colombia (RT-03)."),
]
CustomMessage = Annotated[
    str | None,
    Field(default=None, min_length=1, max_length=MAX_MESSAGE_LENGTH,
          description="Mensaje propio. Sin mensaje, se usa el mensaje por defecto (RF-REC-01)."),
]


class CreateReminderRequest(BaseModel):
    task_id: UUID
    scheduled_at: ScheduledAt
    custom_message: CustomMessage = None


class EditReminderRequest(BaseModel):
    """Los campos ausentes no cambian."""

    scheduled_at: ScheduledAt | None = None
    custom_message: CustomMessage = None


class ReminderResponse(BaseModel):
    """Recordatorio con los nombres de `reminders` (diccionario de datos §7.1)."""

    id: UUID
    task_id: UUID
    scheduled_at: datetime
    custom_message: str | None
    origin: ReminderOrigin
    status: ReminderStatus

    @classmethod
    def from_domain(cls, reminder: Reminder) -> ReminderResponse:
        return cls(
            id=reminder.id,
            task_id=reminder.task_id,
            scheduled_at=reminder.scheduled_at,
            custom_message=reminder.custom_message,
            origin=reminder.origin,
            status=reminder.status,
        )


class ErrorResponse(BaseModel):
    """Cuerpo devuelto por el adaptador cuando la petición falla."""

    detail: str


NOT_FOUND = {404: {"model": ErrorResponse, "description": "El recordatorio o la actividad no existe o no pertenece al usuario."}}
CONFLICT = {409: {"model": ErrorResponse, "description": "El estado del recordatorio o de la actividad no permite la operación."}}
INVALID = {422: {"model": ErrorResponse, "description": "Los datos del recordatorio no son válidos."}}


def _http_error(error: ValueError) -> HTTPException:
    if isinstance(error, (ReminderNotFoundError, ReminderTaskNotFoundError)):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, ReminderStateError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


@dataclass(frozen=True)
class ReminderUseCases:
    create: CreateReminderPort
    list: ListRemindersPort
    get: GetReminderPort
    edit: EditReminderPort
    delete: DeleteReminderPort


_use_cases: ReminderUseCases | None = None


def configure_reminder_use_cases(use_cases: ReminderUseCases) -> None:
    global _use_cases
    _use_cases = use_cases


def _configured() -> ReminderUseCases:
    if _use_cases is None:
        raise RuntimeError("Los casos de uso de Reminders no están configurados.")
    return _use_cases


def get_create_use_case() -> CreateReminderPort:
    return _configured().create


def get_list_use_case() -> ListRemindersPort:
    return _configured().list


def get_get_use_case() -> GetReminderPort:
    return _configured().get


def get_edit_use_case() -> EditReminderPort:
    return _configured().edit


def get_delete_use_case() -> DeleteReminderPort:
    return _configured().delete


@router.post("", status_code=status.HTTP_201_CREATED, responses={**NOT_FOUND, **CONFLICT, **INVALID})
def create_reminder(
    payload: CreateReminderRequest,
    user_id: CurrentUserId,
    use_case: Annotated[CreateReminderPort, Depends(get_create_use_case)],
) -> ReminderResponse:
    try:
        reminder = use_case.execute(user_id, payload.task_id, payload.scheduled_at, payload.custom_message)
    except ValueError as error:
        raise _http_error(error) from error
    return ReminderResponse.from_domain(reminder)


@router.get("")
def list_reminders(
    user_id: CurrentUserId, use_case: Annotated[ListRemindersPort, Depends(get_list_use_case)]
) -> list[ReminderResponse]:
    return [ReminderResponse.from_domain(item) for item in use_case.execute(user_id)]


@router.get("/{reminder_id}", responses=NOT_FOUND)
def get_reminder(
    reminder_id: UUID,
    user_id: CurrentUserId,
    use_case: Annotated[GetReminderPort, Depends(get_get_use_case)],
) -> ReminderResponse:
    try:
        reminder = use_case.execute(reminder_id, user_id)
    except ValueError as error:
        raise _http_error(error) from error
    return ReminderResponse.from_domain(reminder)


@router.patch("/{reminder_id}", responses={**NOT_FOUND, **CONFLICT, **INVALID})
def edit_reminder(
    reminder_id: UUID,
    payload: EditReminderRequest,
    user_id: CurrentUserId,
    use_case: Annotated[EditReminderPort, Depends(get_edit_use_case)],
) -> ReminderResponse:
    try:
        reminder = use_case.execute(reminder_id, user_id, payload.scheduled_at, payload.custom_message)
    except ValueError as error:
        raise _http_error(error) from error
    return ReminderResponse.from_domain(reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, responses={**NOT_FOUND, **CONFLICT})
def delete_reminder(
    reminder_id: UUID,
    user_id: CurrentUserId,
    use_case: Annotated[DeleteReminderPort, Depends(get_delete_use_case)],
) -> None:
    try:
        use_case.execute(reminder_id, user_id)
    except ValueError as error:
        raise _http_error(error) from error
