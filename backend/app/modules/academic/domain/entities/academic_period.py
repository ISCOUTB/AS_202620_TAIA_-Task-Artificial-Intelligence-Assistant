"""Período académico vigente del usuario (RF-ASG-08)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date


class InvalidAcademicPeriodError(ValueError):
    """Las fechas del período no son válidas."""


@dataclass
class AcademicPeriod:
    user_id: uuid.UUID
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date <= self.start_date:
            raise InvalidAcademicPeriodError("La fecha de fin debe ser posterior a la fecha de inicio.")
