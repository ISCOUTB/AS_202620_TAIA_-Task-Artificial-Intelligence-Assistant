"""Plan de estudio de 7 días (RF-EST-01…03, diccionario de datos §6.6 a §6.10)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum

from app.modules.academic.domain.entities.schedule_block import Weekday

EARLIEST_START = time(5, 0)
LATEST_END = time(23, 0)
PLAN_DAYS = 7


class InvalidStudyPlanError(ValueError):
    """Las preferencias del formulario violan una regla de RF-EST-01."""


class StudyPlanStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"


class StudyPreference(str, Enum):
    """Dónde se buscan huecos: entre clases, después de clases o en ambos."""

    BETWEEN_CLASSES = "between_classes"
    AFTER_CLASSES = "after_classes"
    BOTH = "both"


class StudyTimePreference(str, Enum):
    """Momento del día en que el estudiante rinde mejor. Es una preferencia, no una restricción."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ANY = "any"

    def includes(self, moment: time) -> bool:
        if self is StudyTimePreference.MORNING:
            return moment < time(12, 0)
        if self is StudyTimePreference.AFTERNOON:
            return time(12, 0) <= moment < time(18, 0)
        if self is StudyTimePreference.EVENING:
            return moment >= time(18, 0)
        return True


class BusyBlockKind(str, Enum):
    WORK = "work"
    COMMITMENT = "commitment"


@dataclass(frozen=True)
class BusyBlock:
    """Trabajo o compromiso fijo semanal: ninguna sesión cae encima (RF-EST-02)."""

    kind: BusyBlockKind
    weekday: Weekday
    start_time: time
    end_time: time

    def __post_init__(self) -> None:
        if self.end_time <= self.start_time:
            raise InvalidStudyPlanError("La hora de fin de un horario ocupado debe ser posterior a la de inicio.")


@dataclass(frozen=True)
class StudyPreferences:
    """Respuestas del formulario de RF-EST-01, con sus valores por defecto."""

    preference: StudyPreference
    days: frozenset[Weekday] = frozenset(Weekday)
    window_start: time = time(6, 0)
    window_end: time = time(22, 0)
    session_minutes: int = 60
    subject_ids: tuple[uuid.UUID, ...] = ()
    busy_blocks: tuple[BusyBlock, ...] = ()
    max_daily_minutes: int | None = None
    preferred_time: StudyTimePreference = StudyTimePreference.ANY

    def __post_init__(self) -> None:
        if not self.days:
            # Sin días seleccionados se usan todos (RF-EST-01).
            object.__setattr__(self, "days", frozenset(Weekday))
        if self.window_start < EARLIEST_START or self.window_end > LATEST_END:
            raise InvalidStudyPlanError("La franja horaria debe estar entre las 05:00 y las 23:00.")
        if self.window_end <= self.window_start:
            raise InvalidStudyPlanError("El fin de la franja horaria debe ser posterior al inicio.")
        if not 15 <= self.session_minutes <= 240:
            raise InvalidStudyPlanError("Cada sesión debe durar entre 15 y 240 minutos.")
        if self.max_daily_minutes is not None and self.max_daily_minutes < self.session_minutes:
            raise InvalidStudyPlanError("El máximo de minutos por día no puede ser menor que una sesión.")


@dataclass(frozen=True)
class StudySession:
    """Una sesión prepara una actividad o estudia una asignatura en general, nunca las dos."""

    id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    task_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        if (self.task_id is None) == (self.subject_id is None):
            raise InvalidStudyPlanError("Una sesión es de una actividad o de una asignatura, no de ambas.")
        if self.ends_at <= self.starts_at:
            raise InvalidStudyPlanError("Una sesión debe terminar después de empezar.")


@dataclass
class StudyPlan:
    id: uuid.UUID
    user_id: uuid.UUID
    preferences: StudyPreferences
    start_date: date
    sessions: list[StudySession]
    status: StudyPlanStatus = StudyPlanStatus.PROPOSED
    # Actividades que no cupieron en ningún hueco, para avisar al estudiante (RF-EST-02).
    unscheduled_task_ids: list[uuid.UUID] = field(default_factory=list)
