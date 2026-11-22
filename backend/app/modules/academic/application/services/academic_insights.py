"""Implementación de `AcademicInsights`: resumen de un período, horario y asignaturas (RF-AGT-10, 12, 13).

Los conteos, la proyección del horario y la coincidencia de asignaturas los hace
el backend: el LLM no calcula ni compara (RF-AGT-10, RF-AGT-12).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from app.modules.academic.application.ports.inbound.academic_insights import (
    AcademicInsights,
    AcademicPeriodSummary,
    ClassOccurrence,
    SubjectTaskCounts,
)
from app.modules.academic.application.ports.inbound.task_management import AcademicSubjectRef
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from app.modules.academic.application.services.task_management import to_task_data
from app.modules.academic.application.use_cases.academic_calendar import AcademicCalendarUseCase
from app.modules.academic.domain.entities.subject import Subject, normalize_text
from app.modules.academic.domain.entities.task import TaskStatus
from app.shared.clock import Clock, as_bogota, now_bogota


class AcademicInsightsService(AcademicInsights):
    def __init__(
        self,
        tasks: TaskRepository,
        subjects: SubjectRepository,
        calendar: AcademicCalendarUseCase,
        clock: Clock | None = None,
    ) -> None:
        self._tasks = tasks
        self._subjects = subjects
        self._calendar = calendar
        self._now = clock or now_bogota

    def summarize_period(self, user_id: UUID, start: datetime, end: datetime) -> AcademicPeriodSummary:
        """Actividades no eliminadas que vencen en `[start, end)`, por estado y asignatura (RF-AGT-12)."""

        start, end = as_bogota(start), as_bogota(end)
        now = self._now()
        tasks = self._tasks.list_due_between(user_id, start, end)
        names = {s.id: s.name for s in self._subjects.list_by_user(user_id, include_archived=True)}
        counts: dict[UUID, dict[TaskStatus, int]] = {}
        for task in tasks:
            by_status = counts.setdefault(task.subject_id, dict.fromkeys(TaskStatus, 0))
            by_status[task.status(now)] += 1
        by_subject = sorted(
            (
                SubjectTaskCounts(
                    subject_id=subject_id,
                    subject_name=names.get(subject_id, ""),
                    pending=by_status[TaskStatus.PENDING],
                    completed=by_status[TaskStatus.COMPLETED],
                    overdue=by_status[TaskStatus.OVERDUE],
                )
                for subject_id, by_status in counts.items()
            ),
            key=lambda item: normalize_text(item.subject_name),
        )
        next_due = next((task for task in tasks if task.status(now) is TaskStatus.PENDING), None)
        return AcademicPeriodSummary(
            start=start,
            end=end,
            pending=sum(item.pending for item in by_subject),
            completed=sum(item.completed for item in by_subject),
            overdue=sum(item.overdue for item in by_subject),
            by_subject=by_subject,
            next_due=(
                to_task_data(next_due, user_id, names.get(next_due.subject_id, ""), now) if next_due else None
            ),
        )

    def get_classes(self, user_id: UUID, start: datetime, end: datetime) -> list[ClassOccurrence]:
        """Misma proyección que el calendario (RF-AGT-13, RF-TAR-11)."""

        return self._calendar.classes(user_id, start, end)

    def match_subjects(self, user_id: UUID, text: str, limit: int = 5) -> list[AcademicSubjectRef]:
        """Asignaturas activas cuyo nombre o alias coincide con `text` (RF-AGT-10, RF-ASG-09).

        Una coincidencia exacta del nombre o de un alias normalizado gana sobre las
        abreviaturas. Una abreviatura es una secuencia de prefijos de las palabras, en
        orden: "mate básicas" -> "Matemáticas Básicas".
        """

        wanted = normalize_text(text or "")
        if not wanted or limit <= 0:
            return []
        tokens = wanted.split()
        exact: list[AcademicSubjectRef] = []
        partial: list[AcademicSubjectRef] = []
        for subject in self._subjects.list_by_user(user_id):
            known = _known_names(subject)
            if wanted in known:
                exact.append(AcademicSubjectRef(subject_id=subject.id, name=subject.name))
            elif any(_abbreviates(tokens, name.split()) for name in known):
                partial.append(AcademicSubjectRef(subject_id=subject.id, name=subject.name))
        return (exact or partial)[:limit]


def _known_names(subject: Subject) -> list[str]:
    return [subject.normalized_name, *(alias.normalized_alias for alias in subject.aliases)]


def _abbreviates(tokens: list[str], words: Iterable[str]) -> bool:
    """Cada palabra buscada es prefijo de una palabra del nombre, en el mismo orden."""

    remaining = iter(words)
    return all(any(word.startswith(token) for word in remaining) for token in tokens)
