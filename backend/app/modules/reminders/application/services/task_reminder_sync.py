"""Implementación de `TaskReminderSync` y `TaskReminderReader`.

Mantiene los recordatorios coherentes con el ciclo de vida de la actividad
(RF-REC-06, RF-TAR-02, RF-TAR-08) y con la desactivación de la cuenta (RF-USR-09).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from app.modules.reminders.application.errors import InvalidReminderError
from app.modules.reminders.application.ports.inbound.task_reminder_sync import (
    ReminderPlan,
    TaskReminderReader,
    TaskReminderSync,
    TaskReminderView,
)
from app.modules.reminders.application.ports.outbound.academic_task_lookup import AcademicTaskLookup
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.application.reminder_rules import validate_schedule
from app.modules.reminders.domain.entities import Reminder, ReminderOrigin, default_message
from app.modules.reminders.domain.policy import default_schedule
from app.shared.clock import Clock, as_bogota, now_bogota


class TaskReminderSyncService(TaskReminderSync, TaskReminderReader):
    def __init__(
        self, repository: ReminderRepository, tasks: AcademicTaskLookup, clock: Clock = now_bogota
    ) -> None:
        self._repository = repository
        self._tasks = tasks
        self._clock = clock

    def on_task_created(
        self, user_id: UUID, task_id: UUID, due_at: datetime, plan: ReminderPlan
    ) -> None:
        """RF-TAR-02: `none` no crea nada; `default` aplica RF-REC-02; `custom`, RF-REC-01."""

        if plan.mode == "default":
            self._repository.add_all(self._automatic(user_id, task_id, due_at))
        elif plan.mode == "custom":
            self._repository.add_all(self._custom(user_id, task_id, due_at, plan.custom_at))

    def on_due_changed(self, user_id: UUID, task_id: UUID, due_at: datetime) -> None:
        """RF-REC-06: recalcula los automáticos y cancela los personalizados que quedan después."""

        reminders = self._owned(user_id, task_id)
        if any(r.origin is ReminderOrigin.AUTOMATIC for r in reminders):
            self._repository.replace_automatic(task_id, self._automatic(user_id, task_id, due_at))
        due = as_bogota(due_at)
        self._repository.cancel([
            r.id for r in reminders
            if r.origin is ReminderOrigin.CUSTOM and r.is_pending and r.scheduled_at >= due
        ])

    def on_task_closed(self, user_id: UUID, task_id: UUID) -> None:
        """RF-TAR-07 y RF-TAR-10: se cancelan los pendientes."""

        self._repository.cancel([r.id for r in self._owned(user_id, task_id) if r.is_pending])

    def on_task_reopened(self, user_id: UUID, task_id: UUID, due_at: datetime) -> None:
        """RF-TAR-08: regenera los automáticos futuros, si la actividad los tenía."""

        if any(r.origin is ReminderOrigin.AUTOMATIC for r in self._owned(user_id, task_id)):
            self._repository.replace_automatic(task_id, self._automatic(user_id, task_id, due_at))

    def cancel_all_for_user(self, user_id: UUID) -> None:
        """RF-USR-09: ningún recordatorio de una cuenta desactivada genera notificaciones."""

        self._repository.cancel_pending_for_user(user_id)

    def list_for_task(self, user_id: UUID, task_id: UUID) -> list[TaskReminderView]:
        """RF-TAR-05: recordatorios de la actividad ordenados por `scheduled_at`."""

        task = self._tasks.get(task_id, user_id)
        if task is None:
            return []
        fallback = default_message(task.title, task.subject_name, task.due_at)
        return [
            TaskReminderView(
                reminder_id=r.id,
                scheduled_at=r.scheduled_at,
                message=r.custom_message or fallback,
                origin=r.origin.value,
                status=r.status.value,
            )
            for r in self._owned(user_id, task_id)
        ]

    def _owned(self, user_id: UUID, task_id: UUID) -> list[Reminder]:
        return [r for r in self._repository.list_by_task(task_id) if r.user_id == user_id]

    def _automatic(self, user_id: UUID, task_id: UUID, due_at: datetime) -> list[Reminder]:
        return [
            Reminder(id=uuid.uuid4(), user_id=user_id, task_id=task_id, scheduled_at=moment,
                     origin=ReminderOrigin.AUTOMATIC)
            for moment in default_schedule(due_at, self._clock())
        ]

    def _custom(
        self, user_id: UUID, task_id: UUID, due_at: datetime, moments: tuple[datetime, ...]
    ) -> list[Reminder]:
        if not moments:
            raise InvalidReminderError("Indica al menos una fecha para los recordatorios personalizados.")
        now, due = self._clock(), as_bogota(due_at)
        scheduled = sorted({validate_schedule(moment, now, due) for moment in moments})
        return [
            Reminder(id=uuid.uuid4(), user_id=user_id, task_id=task_id, scheduled_at=moment,
                     origin=ReminderOrigin.CUSTOM)
            for moment in scheduled
        ]
