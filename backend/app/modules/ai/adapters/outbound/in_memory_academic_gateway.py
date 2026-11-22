"""AcademicGateway en memoria para las pruebas unitarias del modulo de IA.

No reproduce todas las reglas de academico: solo lo necesario para probar el
caso de uso sin base de datos. La coincidencia de asignaturas es un doble
sencillo de `AcademicInsights.match_subjects` (RF-AGT-10)."""

from __future__ import annotations

import unicodedata
import uuid
from datetime import datetime

from app.modules.ai.application.dto import (
    ClassView,
    NewTask,
    PeriodSummary,
    SubjectCounts,
    SubjectOption,
    TaskChanges,
    TaskFilters,
    TaskView,
)
from app.modules.ai.application.ports.academic_gateway import (
    AcademicGateway,
    TaskDataRejected,
)
from app.modules.ai.domain.messages import MAX_OPTIONS

_MAX_TITLE = 200


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).casefold().split())


class InMemoryAcademicGateway(AcademicGateway):
    def __init__(self) -> None:
        self._by_user: dict[str, list[TaskView]] = {}
        self._subjects: dict[str, list[SubjectOption]] = {}
        self._classes: dict[str, list[ClassView]] = {}

    # -- ayudantes de las pruebas -------------------------------------------

    def add_subject(self, user_id: str, name: str) -> SubjectOption:
        subject = SubjectOption(id=str(uuid.uuid4()), name=name)
        self._subjects.setdefault(user_id, []).append(subject)
        return subject

    def add_task(self, user_id: str, task: TaskView) -> TaskView:
        self._by_user.setdefault(user_id, []).append(task)
        return task

    def add_class(self, user_id: str, item: ClassView) -> ClassView:
        self._classes.setdefault(user_id, []).append(item)
        return item

    # -- AcademicGateway ----------------------------------------------------

    def create_task(self, user_id: str, data: NewTask) -> TaskView:
        title = (data.title or "").strip()
        if not title:
            raise TaskDataRejected("el titulo no puede estar vacio")
        if len(title) > _MAX_TITLE:
            raise TaskDataRejected(f"el titulo supera {_MAX_TITLE} caracteres")
        subject = self._subject(user_id, data.subject_id)

        task = TaskView(
            id=str(uuid.uuid4()),
            title=title,
            due_at=data.due_at,
            subject=subject.name if subject else data.subject,
            status="pending",
            type=data.type,
            subject_id=subject.id if subject else None,
        )
        self._by_user.setdefault(user_id, []).append(task)
        return task

    def list_tasks(self, user_id: str, filters: TaskFilters) -> list[TaskView]:
        found = [task for task in self._by_user.get(user_id, []) if _matches(task, filters)]
        return sorted(found, key=lambda task: task.due_at)

    def update_task(
        self, user_id: str, task_id: str, changes: TaskChanges
    ) -> TaskView:
        subject = self._subject(user_id, changes.subject_id)
        return self._replace(
            user_id,
            task_id,
            lambda task: TaskView(
                id=task.id,
                title=changes.title or task.title,
                due_at=changes.due_at or task.due_at,
                subject=subject.name if subject else task.subject,
                status=task.status,
                priority=task.priority,
                type=task.type,
                subject_id=subject.id if subject else task.subject_id,
            ),
        )

    def complete_task(self, user_id: str, task_id: str) -> TaskView:
        return self._replace(
            user_id,
            task_id,
            lambda task: TaskView(
                id=task.id,
                title=task.title,
                due_at=task.due_at,
                subject=task.subject,
                status="completed",
                type=task.type,
                subject_id=task.subject_id,
            ),
        )

    def match_subjects(self, user_id: str, text: str) -> list[SubjectOption]:
        wanted = _normalize(text)
        if not wanted:
            return []
        exact = [s for s in self._subjects.get(user_id, []) if _normalize(s.name) == wanted]
        if exact:
            return exact[:1]
        return [s for s in self._subjects.get(user_id, []) if wanted in _normalize(s.name)][:MAX_OPTIONS]

    def summarize_period(self, user_id: str, start: datetime, end: datetime) -> PeriodSummary:
        tasks = [t for t in self._by_user.get(user_id, []) if start <= t.due_at < end]
        by_subject: dict[str, list[TaskView]] = {}
        for task in tasks:
            by_subject.setdefault(task.subject or "", []).append(task)
        pending = sorted((t for t in tasks if t.status == "pending"), key=lambda t: t.due_at)
        return PeriodSummary(
            start=start,
            end=end,
            pending=_count(tasks, "pending"),
            completed=_count(tasks, "completed"),
            overdue=_count(tasks, "overdue"),
            by_subject=[
                SubjectCounts(
                    name=name,
                    pending=_count(items, "pending"),
                    completed=_count(items, "completed"),
                    overdue=_count(items, "overdue"),
                )
                for name, items in sorted(by_subject.items())
            ],
            next_due=pending[0] if pending else None,
        )

    def get_classes(self, user_id: str, start: datetime, end: datetime) -> list[ClassView]:
        found = [c for c in self._classes.get(user_id, []) if start <= c.starts_at < end]
        return sorted(found, key=lambda item: item.starts_at)

    # -- internos -----------------------------------------------------------

    def _subject(self, user_id: str, subject_id: str | None) -> SubjectOption | None:
        if subject_id is None:
            return None
        for subject in self._subjects.get(user_id, []):
            if subject.id == subject_id:
                return subject
        raise TaskDataRejected("la asignatura no existe")

    def _replace(self, user_id: str, task_id: str, change) -> TaskView:
        tasks = self._by_user.get(user_id, [])
        for index, task in enumerate(tasks):
            if task.id == task_id:
                tasks[index] = change(task)
                return tasks[index]
        raise TaskDataRejected("la tarea no existe")


def _count(tasks: list[TaskView], status: str) -> int:
    return sum(1 for task in tasks if task.status == status)


def _matches(task: TaskView, filters: TaskFilters) -> bool:
    if filters.text and filters.text.lower() not in task.title.lower():
        return False
    if filters.subject_id and filters.subject_id != task.subject_id:
        return False
    if filters.status and filters.status.lower() != task.status.lower():
        return False
    if filters.type and filters.type != task.type:
        return False
    if filters.due_from and task.due_at < filters.due_from:
        return False
    if filters.due_to and task.due_at > filters.due_to:
        return False
    return True
