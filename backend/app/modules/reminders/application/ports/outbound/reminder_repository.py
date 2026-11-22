"""Puertos de salida de persistencia de `reminders` y `notifications` (diccionario §7)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.modules.reminders.domain.entities import Notification, Reminder


class ReminderRepository(ABC):
    @abstractmethod
    def add_all(self, reminders: list[Reminder]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, reminder_id: UUID) -> Reminder | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        """Ordenados por `scheduled_at`."""
        raise NotImplementedError

    @abstractmethod
    def list_by_task(self, task_id: UUID) -> list[Reminder]:
        """Ordenados por `scheduled_at`."""
        raise NotImplementedError

    @abstractmethod
    def update_pending(self, reminder: Reminder) -> bool:
        """Guarda los cambios solo si sigue `pending`. `False` si ya no lo está."""
        raise NotImplementedError

    @abstractmethod
    def delete_unsent(self, reminder_id: UUID) -> bool:
        """Borra un `pending` o `cancelled` (RF-REC-05). `False` si está `sent`."""
        raise NotImplementedError

    @abstractmethod
    def cancel(self, reminder_ids: list[UUID]) -> int:
        """Pasa a `cancelled` los que sigan `pending`. Devuelve cuántos cambió."""
        raise NotImplementedError

    @abstractmethod
    def cancel_pending_for_user(self, user_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def replace_automatic(self, task_id: UUID, reminders: list[Reminder]) -> None:
        """Borra los automáticos no enviados de la actividad y guarda `reminders`."""
        raise NotImplementedError

    @abstractmethod
    def list_due(self, now: datetime) -> list[Reminder]:
        """`pending` con `scheduled_at <= now`, comparando instantes (RT-03)."""
        raise NotImplementedError

    @abstractmethod
    def claim(self, reminder_id: UUID, notification: Notification) -> bool:
        """`UPDATE ... SET status='sent' WHERE id=:id AND status='pending'` y guarda la
        notificación en la misma transacción. `False` si otro proceso ya lo tomó."""
        raise NotImplementedError


class NotificationRepository(ABC):
    @abstractmethod
    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> tuple[list[Notification], int]:
        """Página de la más reciente a la más antigua y el total."""
        raise NotImplementedError

    @abstractmethod
    def mark_read(self, notification_id: UUID, user_id: UUID, now: datetime) -> Notification | None:
        """Conserva el primer `read_at`. `None` si no existe o es de otro usuario."""
        raise NotImplementedError

    @abstractmethod
    def mark_all_read(self, user_id: UUID, now: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_unread(self, user_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    def record_push(self, notification_id: UUID, attempts: int, sent_at: datetime | None) -> None:
        raise NotImplementedError
