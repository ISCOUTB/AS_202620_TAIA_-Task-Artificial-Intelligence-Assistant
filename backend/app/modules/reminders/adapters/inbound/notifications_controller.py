"""Adaptador HTTP de la bandeja de notificaciones (RF-NOT-03)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.modules.reminders.application.errors import NotificationNotFoundError
from app.modules.reminders.application.ports.inbound.reminder_ports import NotificationInboxPort
from app.modules.reminders.domain.entities import Notification
from app.shared.adapters.inbound.auth import CurrentUserId

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """Notificación con los nombres de `notifications` y el campo derivado `read`."""

    id: UUID
    reminder_id: UUID
    message: str
    created_at: datetime
    read_at: datetime | None
    read: bool

    @classmethod
    def from_domain(cls, notification: Notification) -> NotificationResponse:
        return cls(
            id=notification.id,
            reminder_id=notification.reminder_id,
            message=notification.message,
            created_at=notification.created_at,
            read_at=notification.read_at,
            read=notification.read,
        )


class NotificationPageResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class ErrorResponse(BaseModel):
    """Cuerpo devuelto por el adaptador cuando la petición falla."""

    detail: str


NOT_FOUND = {404: {"model": ErrorResponse, "description": "La notificación no existe o no pertenece al usuario."}}

_inbox: NotificationInboxPort | None = None


def configure_notification_inbox(inbox: NotificationInboxPort) -> None:
    global _inbox
    _inbox = inbox


def get_notification_inbox() -> NotificationInboxPort:
    if _inbox is None:
        raise RuntimeError("La bandeja de notificaciones no está configurada.")
    return _inbox


Inbox = Annotated[NotificationInboxPort, Depends(get_notification_inbox)]


@router.get("")
def list_notifications(
    user_id: CurrentUserId,
    inbox: Inbox,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NotificationPageResponse:
    """De la más reciente a la más antigua."""

    page = inbox.list(user_id, limit, offset)
    return NotificationPageResponse(
        items=[NotificationResponse.from_domain(item) for item in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/unread-count")
def count_unread_notifications(user_id: CurrentUserId, inbox: Inbox) -> UnreadCountResponse:
    return UnreadCountResponse(unread_count=inbox.count_unread(user_id))


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(user_id: CurrentUserId, inbox: Inbox) -> None:
    inbox.mark_all_read(user_id)


@router.patch("/{notification_id}/read", responses=NOT_FOUND)
def mark_notification_read(notification_id: UUID, user_id: CurrentUserId, inbox: Inbox) -> NotificationResponse:
    try:
        notification = inbox.mark_read(notification_id, user_id)
    except NotificationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return NotificationResponse.from_domain(notification)
