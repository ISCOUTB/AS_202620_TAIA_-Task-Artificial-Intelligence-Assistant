"""Adaptador HTTP del plan de estudio (RF-EST-01…03)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.modules.academic.adapters.inbound.structure_api import CONFLICT, INVALID, NOT_FOUND
from app.modules.academic.application.errors import (
    StudyPlanNotFoundError,
    StudyPlanStateError,
    SubjectNotFoundError,
)
from app.modules.academic.application.use_cases.manage_study_plan import (
    ManageStudyPlanUseCase,
    StudyPlanView,
)
from app.modules.academic.domain.entities.schedule_block import Weekday
from app.modules.academic.domain.entities.study_plan import (
    BusyBlock,
    BusyBlockKind,
    InvalidStudyPlanError,
    StudyPreference,
    StudyPreferences,
    StudyTimePreference,
)
from app.shared.adapters.inbound.auth import CurrentUserId

router = APIRouter(prefix="/academic/study-plans", tags=["academic"])

_use_case: ManageStudyPlanUseCase | None = None


def configure_study_plan_use_case(use_case: ManageStudyPlanUseCase) -> None:
    global _use_case
    _use_case = use_case


def get_study_plan_use_case() -> ManageStudyPlanUseCase:
    if _use_case is None:
        raise RuntimeError("El plan de estudio no está configurado.")
    return _use_case


StudyPlans = Annotated[ManageStudyPlanUseCase, Depends(get_study_plan_use_case)]


class BusyBlockBody(BaseModel):
    """Trabajo o compromiso fijo semanal, en hora de Colombia."""

    kind: BusyBlockKind
    weekday: Weekday
    start_time: time
    end_time: time


class StudyPlanRequest(BaseModel):
    """Formulario de RF-EST-01. Lo que no se envía toma su valor por defecto."""

    preference: StudyPreference
    days: list[Weekday] = Field(default_factory=list, description="Vacío: todos los días.")
    window_start: time = time(6, 0)
    window_end: time = time(22, 0)
    session_minutes: int = Field(default=60, ge=15, le=240)
    subject_ids: list[uuid.UUID] = Field(default_factory=list, description="Vacío: todas las activas.")
    busy_blocks: list[BusyBlockBody] = Field(default_factory=list, max_length=30)
    max_daily_minutes: int | None = Field(default=None, ge=15, le=960)
    preferred_time: StudyTimePreference = StudyTimePreference.ANY

    def to_preferences(self) -> StudyPreferences:
        return StudyPreferences(
            preference=self.preference,
            days=frozenset(self.days),
            window_start=self.window_start,
            window_end=self.window_end,
            session_minutes=self.session_minutes,
            subject_ids=tuple(dict.fromkeys(self.subject_ids)),
            busy_blocks=tuple(BusyBlock(b.kind, b.weekday, b.start_time, b.end_time) for b in self.busy_blocks),
            max_daily_minutes=self.max_daily_minutes,
            preferred_time=self.preferred_time,
        )


class StudySessionResponse(BaseModel):
    id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    task_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    title: str
    subject_name: str


class UnscheduledTaskResponse(BaseModel):
    task_id: uuid.UUID
    title: str


class StudyPlanResponse(BaseModel):
    id: uuid.UUID
    status: Literal["proposed", "accepted", "discarded"]
    start_date: date
    preference: StudyPreference
    days: list[Weekday]
    window_start: time
    window_end: time
    session_minutes: int
    subject_ids: list[uuid.UUID]
    busy_blocks: list[BusyBlockBody]
    max_daily_minutes: int | None
    preferred_time: StudyTimePreference
    sessions: list[StudySessionResponse]
    unscheduled: list[UnscheduledTaskResponse] = Field(
        description="Actividades que no cupieron en ningún hueco. Solo se informan al generar el plan."
    )

    @classmethod
    def from_view(cls, view: StudyPlanView) -> "StudyPlanResponse":
        plan, prefs = view.plan, view.plan.preferences
        return cls(
            id=plan.id,
            status=plan.status.value,
            start_date=plan.start_date,
            preference=prefs.preference,
            days=sorted(prefs.days, key=lambda day: day.order),
            window_start=prefs.window_start,
            window_end=prefs.window_end,
            session_minutes=prefs.session_minutes,
            subject_ids=list(prefs.subject_ids),
            busy_blocks=[
                BusyBlockBody(kind=b.kind, weekday=b.weekday, start_time=b.start_time, end_time=b.end_time)
                for b in prefs.busy_blocks
            ],
            max_daily_minutes=prefs.max_daily_minutes,
            preferred_time=prefs.preferred_time,
            sessions=[
                StudySessionResponse(
                    id=item.session.id, starts_at=item.session.starts_at, ends_at=item.session.ends_at,
                    task_id=item.session.task_id, subject_id=item.session.subject_id,
                    title=item.title, subject_name=item.subject_name,
                )
                for item in view.sessions
            ],
            unscheduled=[UnscheduledTaskResponse(task_id=task_id, title=title) for task_id, title in view.unscheduled],
        )


def _http_error(error: ValueError) -> HTTPException:
    if isinstance(error, (StudyPlanNotFoundError, SubjectNotFoundError)):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, StudyPlanStateError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


@router.post("", status_code=status.HTTP_201_CREATED, responses={**NOT_FOUND, **INVALID})
def generate_study_plan(payload: StudyPlanRequest, user_id: CurrentUserId, plans: StudyPlans) -> StudyPlanResponse:
    """Genera un plan propuesto para los próximos 7 días y descarta el propuesto anterior (RF-EST-02)."""

    try:
        plan = plans.generate(user_id, payload.to_preferences())
    except (InvalidStudyPlanError, SubjectNotFoundError) as error:
        raise _http_error(error) from error
    return StudyPlanResponse.from_view(plans.describe(user_id, plan))


@router.get("/current", responses=NOT_FOUND)
def get_current_study_plan(user_id: CurrentUserId, plans: StudyPlans) -> StudyPlanResponse:
    """El plan activo: el propuesto más reciente o, si no hay, el aceptado (RF-EST-03)."""

    try:
        plan = plans.current(user_id)
    except StudyPlanNotFoundError as error:
        raise _http_error(error) from error
    return StudyPlanResponse.from_view(plans.describe(user_id, plan))


@router.post("/{plan_id}/accept", responses={**NOT_FOUND, **CONFLICT})
def accept_study_plan(plan_id: uuid.UUID, user_id: CurrentUserId, plans: StudyPlans) -> StudyPlanResponse:
    """Acepta el plan propuesto y descarta el aceptado anterior (RF-EST-03)."""

    try:
        plan = plans.accept(user_id, plan_id)
    except (StudyPlanNotFoundError, StudyPlanStateError) as error:
        raise _http_error(error) from error
    return StudyPlanResponse.from_view(plans.describe(user_id, plan))


@router.post("/{plan_id}/discard", responses={**NOT_FOUND, **CONFLICT})
def discard_study_plan(plan_id: uuid.UUID, user_id: CurrentUserId, plans: StudyPlans) -> StudyPlanResponse:
    """Descarta el plan (RF-EST-03)."""

    try:
        plan = plans.discard(user_id, plan_id)
    except (StudyPlanNotFoundError, StudyPlanStateError) as error:
        raise _http_error(error) from error
    return StudyPlanResponse.from_view(plans.describe(user_id, plan))
