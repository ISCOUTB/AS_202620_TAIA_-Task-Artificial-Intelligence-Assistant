"""Bloques del horario semanal de clases (RF-ASG-06, RF-ASG-07)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum

from app.shared.clock import now_bogota


class Weekday(str, Enum):
    """Mismo orden que el ENUM `weekday` de PostgreSQL: lunes a domingo."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

    @property
    def order(self) -> int:
        return list(Weekday).index(self)


class InvalidScheduleBlockError(ValueError):
    """Los datos del bloque de horario violan una regla del dominio."""


@dataclass
class ScheduleBlock:
    """Horas de reloj en Colombia (`time` sin zona), según el diccionario de datos."""

    id: uuid.UUID
    subject_id: uuid.UUID
    weekday: Weekday
    start_time: time
    end_time: time
    room: str | None = None
    created_at: datetime = field(default_factory=now_bogota)

    MAX_ROOM_LENGTH = 50

    @staticmethod
    def create(
        subject_id: uuid.UUID,
        weekday: Weekday,
        start_time: time,
        end_time: time,
        room: str | None = None,
    ) -> "ScheduleBlock":
        block = ScheduleBlock(
            id=uuid.uuid4(),
            subject_id=subject_id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            room=_clean_room(room),
        )
        block._validate_times()
        return block

    def update(
        self,
        weekday: Weekday | None = None,
        start_time: time | None = None,
        end_time: time | None = None,
        room: str | None = None,
    ) -> None:
        if weekday is not None:
            self.weekday = weekday
        if start_time is not None:
            self.start_time = start_time
        if end_time is not None:
            self.end_time = end_time
        if room is not None:
            self.room = _clean_room(room)
        self._validate_times()

    def overlaps(self, other: "ScheduleBlock") -> bool:
        return (
            self.id != other.id
            and self.weekday == other.weekday
            and self.start_time < other.end_time
            and other.start_time < self.end_time
        )

    def _validate_times(self) -> None:
        if self.end_time <= self.start_time:
            raise InvalidScheduleBlockError("La hora de fin debe ser posterior a la hora de inicio.")


def _clean_room(room: str | None) -> str | None:
    clean = " ".join((room or "").split())
    if len(clean) > ScheduleBlock.MAX_ROOM_LENGTH:
        raise InvalidScheduleBlockError(f"El aula no puede superar {ScheduleBlock.MAX_ROOM_LENGTH} caracteres.")
    return clean or None
