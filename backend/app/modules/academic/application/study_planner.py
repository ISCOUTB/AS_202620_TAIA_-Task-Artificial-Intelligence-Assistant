"""Reglas de RF-EST-02: huecos libres y colocación de las sesiones.

No depende del LLM. El LLM solo sugiere qué actividad va en cada hueco; estas
funciones descartan lo que viole una regla y reubican lo que falte, así que el
plan cumple las reglas con o sin el LLM.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.modules.academic.domain.entities.schedule_block import Weekday
from app.modules.academic.domain.entities.study_plan import (
    PLAN_DAYS,
    StudyPreference,
    StudyPreferences,
    StudySession,
)
from app.shared.clock import BOGOTA_TZ, as_bogota

SLOT_ALIGNMENT_MINUTES = 15
HIGH_PRIORITY_SESSIONS = 2

Interval = tuple[datetime, datetime]


@dataclass(frozen=True)
class FreeSlot:
    """Hueco libre del tamaño de una sesión, numerado para el LLM."""

    index: int
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class PlanItem:
    """Actividad pendiente que recibe sesiones, numerada para el LLM."""

    index: int
    task_id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    subject_name: str
    due_at: datetime
    priority: str | None

    @property
    def sessions(self) -> int:
        """Las de prioridad alta reciben dos sesiones; las demás, una (RF-EST-02)."""

        return HIGH_PRIORITY_SESSIONS if self.priority == "high" else 1


@dataclass(frozen=True)
class Placement:
    sessions: list[StudySession]
    unscheduled_task_ids: list[uuid.UUID]


def plan_days(start: date, preferences: StudyPreferences) -> list[date]:
    """Los 7 días del plan que el estudiante marcó como disponibles."""

    days = (start + timedelta(days=offset) for offset in range(PLAN_DAYS))
    return [day for day in days if list(Weekday)[day.weekday()] in preferences.days]


def free_slots(
    preferences: StudyPreferences,
    now: datetime,
    start: date,
    classes: Sequence[Interval],
) -> list[FreeSlot]:
    """Huecos de `session_minutes` dentro de la franja, sin clases, trabajo ni compromisos."""

    now = as_bogota(now)
    slots: list[FreeSlot] = []
    for day in plan_days(start, preferences):
        day_classes = sorted(
            (as_bogota(a), as_bogota(b)) for a, b in classes if as_bogota(a).date() == day
        )
        allowed = _allowed_range(day, preferences, day_classes)
        if allowed is None:
            continue
        first, last = allowed
        first = max(first, _align(now))
        weekday = list(Weekday)[day.weekday()]
        busy = [
            *day_classes,
            *(
                (_at(day, block.start_time), _at(day, block.end_time))
                for block in preferences.busy_blocks
                if block.weekday is weekday
            ),
        ]
        for a, b in _subtract((first, last), busy):
            moment = _align(a)
            length = timedelta(minutes=preferences.session_minutes)
            while moment + length <= b:
                slots.append(FreeSlot(len(slots), moment, moment + length))
                moment += length
    return slots


def place_sessions(
    preferences: StudyPreferences,
    slots: Sequence[FreeSlot],
    items: Sequence[PlanItem],
    proposals: Iterable[tuple[int, int]],
    general_subject_ids: Sequence[uuid.UUID] = (),
) -> Placement:
    """Coloca las sesiones respetando las reglas; las propuestas del LLM van primero.

    Las actividades de prioridad alta eligen hueco antes que las demás. Una
    propuesta que viola una regla se descarta, y lo que falte se reubica en el
    mejor hueco válido: primero el momento preferido del día y un día distinto
    al de otra sesión de la misma actividad, después el más temprano.
    """

    by_index = {slot.index: slot for slot in slots}
    suggested: dict[int, list[FreeSlot]] = {}
    for item_index, slot_index in proposals:
        slot = by_index.get(slot_index)
        if slot is not None:
            suggested.setdefault(item_index, []).append(slot)

    used: set[int] = set()
    minutes_per_day: dict[date, int] = {}
    sessions: list[StudySession] = []
    unscheduled: list[uuid.UUID] = []

    def fits(slot: FreeSlot, due_at: datetime | None) -> bool:
        if slot.index in used:
            return False
        if due_at is not None and slot.ends_at > as_bogota(due_at):
            return False
        cap = preferences.max_daily_minutes
        taken = minutes_per_day.get(slot.starts_at.date(), 0)
        return cap is None or taken + preferences.session_minutes <= cap

    def take(slot: FreeSlot, task_id: uuid.UUID | None, subject_id: uuid.UUID | None) -> None:
        used.add(slot.index)
        day = slot.starts_at.date()
        minutes_per_day[day] = minutes_per_day.get(day, 0) + preferences.session_minutes
        sessions.append(StudySession(uuid.uuid4(), slot.starts_at, slot.ends_at, task_id, subject_id))

    def best(due_at: datetime | None, avoid_days: set[date]) -> FreeSlot | None:
        candidates = [slot for slot in slots if fits(slot, due_at)]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda slot: (
                slot.starts_at.date() in avoid_days,
                not preferences.preferred_time.includes(slot.starts_at.time()),
                slot.starts_at,
            ),
        )

    ordered = sorted(items, key=lambda item: (item.priority != "high", as_bogota(item.due_at)))
    for item in ordered:
        days: set[date] = set()
        for slot in suggested.get(item.index, []):
            if len(days) < item.sessions and fits(slot, item.due_at) and slot.starts_at.date() not in days:
                take(slot, item.task_id, None)
                days.add(slot.starts_at.date())
        placed = len(days)
        while placed < item.sessions:
            slot = best(item.due_at, days)
            if slot is None:
                break
            take(slot, item.task_id, None)
            days.add(slot.starts_at.date())
            placed += 1
        if placed == 0:
            unscheduled.append(item.task_id)

    for subject_id in general_subject_ids:
        slot = best(None, set())
        if slot is None:
            break
        take(slot, None, subject_id)

    return Placement(sorted(sessions, key=lambda s: s.starts_at), unscheduled)


def _allowed_range(day: date, preferences: StudyPreferences, classes: list[Interval]) -> Interval | None:
    """Franja del día según la preferencia: entre clases, después de clases o ambas."""

    window = (_at(day, preferences.window_start), _at(day, preferences.window_end))
    if preferences.preference is StudyPreference.BOTH:
        return window
    if preferences.preference is StudyPreference.BETWEEN_CLASSES:
        if len(classes) < 2:
            return None
        start, end = classes[0][0], max(b for _, b in classes)
    else:
        start = max(b for _, b in classes) if classes else window[0]
        end = window[1]
    start, end = max(start, window[0]), min(end, window[1])
    return (start, end) if end > start else None


def _subtract(interval: Interval, busy: Iterable[Interval]) -> list[Interval]:
    free = [interval]
    for b_start, b_end in sorted(busy):
        next_free = []
        for a, b in free:
            if b_end <= a or b_start >= b:
                next_free.append((a, b))
                continue
            if b_start > a:
                next_free.append((a, b_start))
            if b_end < b:
                next_free.append((b_end, b))
        free = next_free
    return free


def _at(day: date, moment: time) -> datetime:
    return datetime.combine(day, moment, tzinfo=BOGOTA_TZ)


def _align(moment: datetime) -> datetime:
    """Redondea hacia arriba al cuarto de hora, para que las sesiones empiecen en horas limpias."""

    moment = as_bogota(moment)
    if moment.second or moment.microsecond:
        moment = moment.replace(second=0, microsecond=0) + timedelta(minutes=1)
    extra = moment.minute % SLOT_ALIGNMENT_MINUTES
    return moment if extra == 0 else moment + timedelta(minutes=SLOT_ALIGNMENT_MINUTES - extra)
