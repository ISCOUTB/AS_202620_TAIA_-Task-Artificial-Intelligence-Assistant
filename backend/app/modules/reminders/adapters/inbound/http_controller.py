from datetime import datetime
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from backend.app.modules.academic.adapters.outbound.repository_provider import get_task_repository
from backend.app.modules.usuario.adapters.inbound.api import get_authenticated_user_id
from backend.app.modules.reminders.adapters.outbound.academic_task_lookup_adapter import AcademicTaskLookupAdapter
from backend.app.modules.reminders.adapters.outbound.repository_provider import get_reminder_repository
from backend.app.modules.reminders.application.ports.inbound.reminder_ports import (
    CreateReminderPort, DeleteReminderPort, EditReminderPort, GetReminderPort,
    ListRemindersPort, MarkReminderCompletedPort, ScheduleNotificationPort, SendNotificationPort,
)
from backend.app.modules.reminders.application.use_cases.create_reminder import CreateReminderUseCase
from backend.app.modules.reminders.application.use_cases.delete_reminder import DeleteReminderUseCase
from backend.app.modules.reminders.application.use_cases.edit_reminder import EditReminderUseCase
from backend.app.modules.reminders.application.use_cases.get_reminder import GetReminderUseCase
from backend.app.modules.reminders.application.use_cases.list_reminders import ListRemindersUseCase
from backend.app.modules.reminders.application.use_cases.mark_reminder_completed import MarkReminderCompletedUseCase
from backend.app.modules.reminders.application.use_cases.schedule_notification import ScheduleNotificationUseCase
from backend.app.modules.reminders.application.use_cases.send_notification import SendNotificationUseCase
from backend.app.modules.reminders.adapters.outbound.notification_provider import get_notification_sender
from backend.app.modules.reminders.domain.entities import Reminder

router = APIRouter(prefix='/reminders', tags=['reminders'])
CurrentUserId = Annotated[UUID, Depends(get_authenticated_user_id)]

class CreateReminderRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    scheduled_at: datetime
    task_id: UUID
class EditReminderRequest(BaseModel):
    message: str | None = Field(default=None, min_length=1, max_length=500)
    scheduled_at: datetime | None = None
class ReminderResponse(BaseModel):
    id: int
    user_id: UUID
    message: str
    scheduled_at: datetime
    is_completed: bool
    task_id: UUID
    @classmethod
    def from_domain(cls, reminder: Reminder) -> 'ReminderResponse':
        return cls.model_validate(reminder.model_dump())

def _task_lookup() -> AcademicTaskLookupAdapter:
    repository = get_task_repository()
    return AcademicTaskLookupAdapter(repository.get_by_id)

def get_create_use_case() -> CreateReminderPort:
    return CreateReminderUseCase(get_reminder_repository(), _task_lookup())
def get_list_use_case() -> ListRemindersPort:
    return ListRemindersUseCase(get_reminder_repository())
def get_get_use_case() -> GetReminderPort:
    return GetReminderUseCase(get_reminder_repository())
def get_edit_use_case() -> EditReminderPort:
    return EditReminderUseCase(get_reminder_repository())
def get_delete_use_case() -> DeleteReminderPort:
    return DeleteReminderUseCase(get_reminder_repository())
def get_complete_use_case() -> MarkReminderCompletedPort:
    return MarkReminderCompletedUseCase(get_reminder_repository())


def get_schedule_notification_use_case() -> ScheduleNotificationPort:
    return ScheduleNotificationUseCase(get_reminder_repository())


def get_send_notification_use_case() -> SendNotificationPort:
    return SendNotificationUseCase(get_notification_sender())

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
def get_reminder(reminder_id: int, user_id: CurrentUserId, use_case: Annotated[GetReminderPort, Depends(get_get_use_case)]) -> ReminderResponse:
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
def edit_reminder(reminder_id: int, payload: EditReminderRequest, user_id: CurrentUserId, use_case: Annotated[EditReminderPort, Depends(get_edit_use_case)]) -> ReminderResponse:
    try:
        reminder = use_case.execute(reminder_id, user_id, payload.message, payload.scheduled_at)
    except ValueError as error:
        raise HTTPException(status_code=422 if 'no encontrado' not in str(error).lower() else 404, detail=str(error)) from error
    return ReminderResponse.from_domain(reminder)

@router.delete(
    '/{reminder_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {'model': ErrorResponse, 'description': 'El recordatorio no existe o no pertenece al usuario.'}},
)
def delete_reminder(reminder_id: int, user_id: CurrentUserId, use_case: Annotated[DeleteReminderPort, Depends(get_delete_use_case)]) -> None:
    try:
        use_case.execute(reminder_id, user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

@router.post(
    '/{reminder_id}/complete',
    responses={404: {'model': ErrorResponse, 'description': 'El recordatorio no existe o no pertenece al usuario.'}},
)
def mark_reminder_completed(reminder_id: int, user_id: CurrentUserId, use_case: Annotated[MarkReminderCompletedPort, Depends(get_complete_use_case)]) -> ReminderResponse:
    try:
        reminder = use_case.execute(reminder_id, user_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ReminderResponse.from_domain(reminder)


class NotificationResponse(BaseModel):
    reminder_id: int
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
    reminder_id: int,
    user_id: CurrentUserId,
    schedule_use_case: Annotated[ScheduleNotificationPort, Depends(get_schedule_notification_use_case)],
    send_use_case: Annotated[SendNotificationPort, Depends(get_send_notification_use_case)],
) -> NotificationResponse:
    # First enforce ownership using the same application use case as the CRUD read path.
    try:
        reminder = GetReminderUseCase(get_reminder_repository()).execute(reminder_id, user_id)
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
