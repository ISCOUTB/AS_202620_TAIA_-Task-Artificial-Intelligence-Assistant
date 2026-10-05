from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.shared.adapters.inbound.auth import CurrentUserId
from app.modules.reminders.application.errors import ReminderNotFoundError
from app.modules.reminders.application.ports.inbound.reminder_ports import (
    CreateReminderPort, DeleteReminderPort, EditReminderPort, GetReminderPort,
    ListRemindersPort, MarkReminderCompletedPort, ScheduleNotificationPort, SendNotificationPort,
)
from app.modules.reminders.domain.entities import Reminder

router = APIRouter(prefix='/reminders', tags=['reminders'])
class CreateReminderRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    scheduled_at: datetime
    task_id: UUID
class EditReminderRequest(BaseModel):
    message: str | None = Field(default=None, min_length=1, max_length=500)
    scheduled_at: datetime | None = None
class ReminderResponse(BaseModel):
    id: UUID
    user_id: UUID
    message: str
    scheduled_at: datetime
    is_completed: bool
    task_id: UUID
    @classmethod
    def from_domain(cls, reminder: Reminder) -> 'ReminderResponse':
        return cls.model_validate(reminder.model_dump())

@dataclass(frozen=True)
class ReminderUseCases:
    create: CreateReminderPort
    list: ListRemindersPort
    get: GetReminderPort
    edit: EditReminderPort
    delete: DeleteReminderPort
    complete: MarkReminderCompletedPort
    schedule_notification: ScheduleNotificationPort
    send_notification: SendNotificationPort


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


def get_complete_use_case() -> MarkReminderCompletedPort:
    return _configured().complete


def get_schedule_notification_use_case() -> ScheduleNotificationPort:
    return _configured().schedule_notification


def get_send_notification_use_case() -> SendNotificationPort:
    return _configured().send_notification


class ErrorResponse(BaseModel):
    '''Cuerpo devuelto por el adaptador cuando la petición falla.'''

    detail: str


@router.post(
    '',
    status_code=status.HTTP_201_CREATED,
    responses={422: {'model': ErrorResponse, 'description': 'Los datos del recordatorio no son válidos.'}},
)
def create_reminder(payload: CreateReminderRequest, user_id: CurrentUserId, use_case: Annotated[CreateReminderPort, Depends(get_create_use_case)]) -> ReminderResponse:
    try:
        reminder = use_case.execute(user_id, payload.message, payload.scheduled_at, payload.task_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ReminderResponse.from_domain(reminder)

@router.get('')
def list_reminders(user_id: CurrentUserId, use_case: Annotated[ListRemindersPort, Depends(get_list_use_case)]) -> list[ReminderResponse]:
    return [ReminderResponse.from_domain(item) for item in use_case.execute(user_id)]

@router.get(
    '/{reminder_id}',
    responses={404: {'model': ErrorResponse, 'description': 'El recordatorio no existe o no pertenece al usuario.'}},
)
def get_reminder(reminder_id: UUID, user_id: CurrentUserId, use_case: Annotated[GetReminderPort, Depends(get_get_use_case)]) -> ReminderResponse:
    try:
        reminder = use_case.execute(reminder_id, user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ReminderResponse.from_domain(reminder)

@router.patch(
    '/{reminder_id}',
    responses={
        404: {'model': ErrorResponse, 'description': 'El recordatorio no existe o no pertenece al usuario.'},
        422: {'model': ErrorResponse, 'description': 'Los datos del recordatorio no son válidos.'},
    },
)
def edit_reminder(reminder_id: UUID, payload: EditReminderRequest, user_id: CurrentUserId, use_case: Annotated[EditReminderPort, Depends(get_edit_use_case)]) -> ReminderResponse:
    try:
        reminder = use_case.execute(reminder_id, user_id, payload.message, payload.scheduled_at)
    except ReminderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ReminderResponse.from_domain(reminder)

@router.delete(
    '/{reminder_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {'model': ErrorResponse, 'description': 'El recordatorio no existe o no pertenece al usuario.'}},
)
def delete_reminder(reminder_id: UUID, user_id: CurrentUserId, use_case: Annotated[DeleteReminderPort, Depends(get_delete_use_case)]) -> None:
    try:
        use_case.execute(reminder_id, user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

@router.post(
    '/{reminder_id}/complete',
    responses={404: {'model': ErrorResponse, 'description': 'El recordatorio no existe o no pertenece al usuario.'}},
)
def mark_reminder_completed(reminder_id: UUID, user_id: CurrentUserId, use_case: Annotated[MarkReminderCompletedPort, Depends(get_complete_use_case)]) -> ReminderResponse:
    try:
        reminder = use_case.execute(reminder_id, user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ReminderResponse.from_domain(reminder)


class NotificationResponse(BaseModel):
    reminder_id: UUID
    sent: bool
    scheduled_at: datetime


@router.post(
    '/{reminder_id}/notify',
    responses={
        404: {'model': ErrorResponse, 'description': 'El recordatorio no existe o no pertenece al usuario.'},
        503: {'model': ErrorResponse, 'description': 'No se pudo entregar la notificación por Telegram.'},
    },
)
def notify_reminder(
    reminder_id: UUID,
    user_id: CurrentUserId,
    read_use_case: Annotated[GetReminderPort, Depends(get_get_use_case)],
    schedule_use_case: Annotated[ScheduleNotificationPort, Depends(get_schedule_notification_use_case)],
    send_use_case: Annotated[SendNotificationPort, Depends(get_send_notification_use_case)],
) -> NotificationResponse:
    # First enforce ownership using the same application use case as the CRUD read path.
    try:
        reminder = read_use_case.execute(reminder_id, user_id)
        notification = schedule_use_case.execute(reminder.id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    sent = send_use_case.execute(notification)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                'No se pudo enviar la notificación por Telegram. ' 
                'Verifica que la cuenta esté vinculada y que TAIA_TELEGRAM_BOT_TOKEN esté configurado.'
            ),
        )

    return NotificationResponse(
        reminder_id=notification.reminder_id,
        sent=True,
        scheduled_at=notification.date_send,
    )
