"""Puerto de persistencia del período académico."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.modules.academic.domain.entities.academic_period import AcademicPeriod


class AcademicPeriodRepository(ABC):
    @abstractmethod
    def get(self, user_id: uuid.UUID) -> AcademicPeriod | None:
        """Período vigente del usuario, si lo definió."""

    @abstractmethod
    def save(self, period: AcademicPeriod) -> None:
        """Crea o reemplaza el período del usuario."""
