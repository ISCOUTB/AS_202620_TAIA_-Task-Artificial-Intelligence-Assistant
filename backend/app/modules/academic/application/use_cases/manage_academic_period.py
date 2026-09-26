"""Casos de uso del período académico (RF-ASG-08)."""

from __future__ import annotations

import uuid
from datetime import date

from app.modules.academic.application.errors import AcademicPeriodNotFoundError
from app.modules.academic.application.ports.outbound.academic_period_repository import (
    AcademicPeriodRepository,
)
from app.modules.academic.domain.entities.academic_period import AcademicPeriod


class ManageAcademicPeriodUseCase:
    def __init__(self, periods: AcademicPeriodRepository) -> None:
        self._periods = periods

    def get(self, user_id: uuid.UUID) -> AcademicPeriod:
        period = self._periods.get(user_id)
        if period is None:
            raise AcademicPeriodNotFoundError("No has definido un período académico.")
        return period

    def set(self, user_id: uuid.UUID, start_date: date, end_date: date) -> AcademicPeriod:
        period = AcademicPeriod(user_id=user_id, start_date=start_date, end_date=end_date)
        self._periods.save(period)
        return period
