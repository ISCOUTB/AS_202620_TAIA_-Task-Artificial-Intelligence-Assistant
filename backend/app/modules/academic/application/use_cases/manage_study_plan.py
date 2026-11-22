"""RF-EST-01…03 · Generar, consultar, aceptar y descartar el plan de estudio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta

from app.modules.academic.application.errors import (
    StudyPlanNotFoundError,
    StudyPlanStateError,
    SubjectNotFoundError,
)
from app.modules.academic.application.ports.outbound.study_plan_repository import StudyPlanRepository
from app.modules.academic.application.ports.outbound.study_session_advisor import StudySessionAdvisor
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from app.modules.academic.application.study_planner import (
    PlanItem,
    free_slots,
    place_sessions,
)
from app.modules.academic.application.use_cases.academic_calendar import AcademicCalendarUseCase
from app.modules.academic.domain.entities.study_plan import (
    PLAN_DAYS,
    StudyPlan,
    StudyPlanStatus,
    StudyPreference,
    StudyPreferences,
    StudySession,
)
from app.shared.clock import BOGOTA_TZ, Clock, now_bogota

# Hasta dónde se buscan actividades pendientes: las que vencen después del plan
# también reciben sesiones si son de prioridad alta o media.
_LOOKAHEAD = timedelta(days=60)


@dataclass(frozen=True)
class SessionView:
    session: StudySession
    title: str
    subject_name: str


@dataclass(frozen=True)
class StudyPlanView:
    """El plan con los nombres que muestra la aplicación."""

    plan: StudyPlan
    sessions: list[SessionView]
    unscheduled: list[tuple[uuid.UUID, str]]


GENERAL_SESSION_TITLE = "Repaso general"


class ManageStudyPlanUseCase:
    def __init__(
        self,
        plans: StudyPlanRepository,
        tasks: TaskRepository,
        subjects: SubjectRepository,
        calendar: AcademicCalendarUseCase,
        advisor: StudySessionAdvisor,
        clock: Clock | None = None,
    ) -> None:
        self._plans = plans
        self._tasks = tasks
        self._subjects = subjects
        self._calendar = calendar
        self._advisor = advisor
        self._now = clock or now_bogota

    def generate(self, user_id: uuid.UUID, preferences: StudyPreferences) -> StudyPlan:
        """RF-EST-02: huecos libres de los próximos 7 días, sugerencia del LLM y reglas del backend."""

        now = self._now()
        start = now.date()
        active = {s.id: s.name for s in self._subjects.list_by_user(user_id)}
        included = list(preferences.subject_ids) or list(active)
        if any(subject_id not in active for subject_id in included):
            raise SubjectNotFoundError("Una de las asignaturas no existe o está archivada.")
        preferences = _with_subjects(preferences, tuple(included))

        day_start = datetime.combine(start, time(0, 0), tzinfo=BOGOTA_TZ)
        classes = [
            (occurrence.starts_at, occurrence.ends_at)
            for occurrence in self._calendar.classes(user_id, day_start, day_start + timedelta(days=PLAN_DAYS))
        ]
        slots = free_slots(preferences, now, start, classes)

        pending = [
            task
            for task in self._tasks.list_due_between(user_id, now, now + _LOOKAHEAD)
            if task.completed_at is None and task.subject_id in included
        ]
        items = [
            PlanItem(
                index=index,
                task_id=task.id,
                subject_id=task.subject_id,
                title=task.title,
                subject_name=active[task.subject_id],
                due_at=task.due_at,
                priority=_priority(task, now),
            )
            for index, task in enumerate(pending)
        ]
        proposals = self._advisor.propose(slots, items) if slots and items else []
        busy_subjects = {item.subject_id for item in items}
        placement = place_sessions(
            preferences, slots, items, proposals,
            general_subject_ids=[subject_id for subject_id in included if subject_id not in busy_subjects],
        )
        plan = StudyPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            preferences=preferences,
            start_date=start,
            sessions=placement.sessions,
            unscheduled_task_ids=placement.unscheduled_task_ids,
        )
        self._plans.add(plan)
        return plan

    def current(self, user_id: uuid.UUID) -> StudyPlan:
        plan = self._plans.current(user_id)
        if plan is None:
            raise StudyPlanNotFoundError("Aún no tienes un plan de estudio.")
        return plan

    def accept(self, user_id: uuid.UUID, plan_id: uuid.UUID) -> StudyPlan:
        plan = self._owned(user_id, plan_id)
        if plan.status is not StudyPlanStatus.PROPOSED or not self._plans.accept(plan_id, user_id):
            raise StudyPlanStateError("Solo se puede aceptar un plan propuesto.")
        return self._owned(user_id, plan_id)

    def discard(self, user_id: uuid.UUID, plan_id: uuid.UUID) -> StudyPlan:
        plan = self._owned(user_id, plan_id)
        if plan.status is StudyPlanStatus.DISCARDED or not self._plans.discard(plan_id, user_id):
            raise StudyPlanStateError("El plan ya estaba descartado.")
        return self._owned(user_id, plan_id)

    def describe(self, user_id: uuid.UUID, plan: StudyPlan) -> StudyPlanView:
        """Títulos y asignaturas de las sesiones, leídos del propio módulo."""

        names = {s.id: s.name for s in self._subjects.list_by_user(user_id, include_archived=True)}
        titles: dict[uuid.UUID, tuple[str, uuid.UUID]] = {}

        def task_info(task_id: uuid.UUID) -> tuple[str, uuid.UUID | None]:
            if task_id not in titles:
                task = self._tasks.get(task_id, user_id)
                titles[task_id] = (task.title, task.subject_id) if task else ("Actividad eliminada", None)
            return titles[task_id]

        sessions = []
        for session in plan.sessions:
            if session.task_id is not None:
                title, subject_id = task_info(session.task_id)
            else:
                title, subject_id = GENERAL_SESSION_TITLE, session.subject_id
            sessions.append(SessionView(session, title, names.get(subject_id, "")))
        unscheduled = [(task_id, task_info(task_id)[0]) for task_id in plan.unscheduled_task_ids]
        return StudyPlanView(plan, sessions, unscheduled)

    def calendar_sessions(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[SessionView]:
        """Sesiones del plan aceptado para el calendario (RF-EST-03, RF-TAR-11)."""

        plan = StudyPlan(
            id=uuid.uuid4(), user_id=user_id, preferences=StudyPreferences(preference=StudyPreference.BOTH),
            start_date=start.date(), sessions=self._plans.accepted_sessions(user_id, start, end),
        )
        return self.describe(user_id, plan).sessions

    def _owned(self, user_id: uuid.UUID, plan_id: uuid.UUID) -> StudyPlan:
        plan = self._plans.get(plan_id, user_id)
        if plan is None:
            raise StudyPlanNotFoundError("El plan de estudio no existe.")
        return plan


def _with_subjects(preferences: StudyPreferences, subject_ids: tuple[uuid.UUID, ...]) -> StudyPreferences:
    """Sin asignaturas seleccionadas se guardan todas las activas (RF-EST-01)."""

    return replace(preferences, subject_ids=subject_ids)


def _priority(task, now: datetime) -> str | None:
    priority = task.priority(now)
    return priority.value if priority else None
