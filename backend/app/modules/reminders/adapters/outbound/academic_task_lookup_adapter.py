"""Lee las actividades mediante el puerto público de Academic (P-B-02)."""

from __future__ import annotations

from uuid import UUID

from app.modules.academic.application.ports.inbound.task_management import AcademicTaskManagement
from app.modules.reminders.application.ports.outbound.academic_task_lookup import (
    AcademicTaskLookup,
    TaskInfo,
)


class AcademicTaskLookupAdapter(AcademicTaskLookup):
    def __init__(self, academic: AcademicTaskManagement) -> None:
        self._academic = academic

    def get(self, task_id: UUID, user_id: UUID) -> TaskInfo | None:
        try:
            task = self._academic.get_task(task_id, user_id)
        except ValueError:
            # Academic lanza TaskNotFoundError (un ValueError) si no existe, está
            # eliminada o es de otro usuario.
            return None
        return TaskInfo(
            task_id=task.task_id,
            title=task.title,
            subject_name=task.subject_name,
            due_at=task.due_at,
            completed=task.completed_at is not None,
        )
