"""AcademicGateway en memoria para pruebas y ejecucion local sin el modulo
academico real. Se sustituye por el adaptador real cuando este disponible
(ver context_IA.md, Fase 5)."""

from __future__ import annotations

import uuid
from dataclasses import replace

from backend.app.modules.ai.application.dto import (
    NewTask,
    TaskChanges,
    TaskFilters,
    TaskView,
)
from backend.app.modules.ai.application.ports.academic_gateway import (
    AcademicGateway,
    TaskDataRejected,
)

_MAX_TITLE = 200


class InMemoryAcademicGateway(AcademicGateway):
    def __init__(self) -> None:
        self._by_user: dict[str, list[TaskView]] = {}

    def create_task(self, user_id: str, data: NewTask) -> TaskView:
        title = (data.title or "").strip()
        if not title:
            raise TaskDataRejected("el titulo no puede estar vacio")
        if len(title) > _MAX_TITLE:
            raise TaskDataRejected(f"el titulo supera {_MAX_TITLE} caracteres")

        task = TaskView(
            id=str(uuid.uuid4()),
            title=title,
            due_at=data.due_at,
            subject=data.subject,
            status="pending",
        )
        self._by_user.setdefault(user_id, []).append(task)
        return task

    def list_tasks(self, user_id: str, filters: TaskFilters) -> list[TaskView]:
        return [
            task
            for task in self._by_user.get(user_id, [])
            if _matches(task, filters)
        ]

    def update_task(
        self, user_id: str, task_id: str, changes: TaskChanges
    ) -> TaskView:
        tasks = self._by_user.get(user_id, [])
        for index, task in enumerate(tasks):
            if task.id == task_id:
                updated = replace(
                    task,
                    title=changes.title or task.title,
                    due_at=changes.due_at or task.due_at,
                    subject=(
                        changes.subject
                        if changes.subject is not None
                        else task.subject
                    ),
                )
                tasks[index] = updated
                return updated
        raise TaskDataRejected("la tarea no existe")


def _matches(task: TaskView, filters: TaskFilters) -> bool:
    if filters.text and filters.text.lower() not in task.title.lower():
        return False
    if filters.subject and filters.subject.lower() != (task.subject or "").lower():
        return False
    if filters.status and filters.status.lower() != task.status.lower():
        return False
    if filters.due_from and task.due_at < filters.due_from:
        return False
    if filters.due_to and task.due_at > filters.due_to:
        return False
    return True
