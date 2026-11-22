"""Puerto de persistencia de los planes de estudio (diccionario §6.6 a §6.10)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.academic.domain.entities.study_plan import StudyPlan, StudySession


class StudyPlanRepository(ABC):
    @abstractmethod
    def add(self, plan: StudyPlan) -> None:
        """Guarda un plan propuesto y descarta, en la misma transacción, el propuesto anterior (RF-EST-03)."""

    @abstractmethod
    def get(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> StudyPlan | None:
        """El plan solo si es del usuario (RT-02)."""

    @abstractmethod
    def current(self, user_id: uuid.UUID) -> StudyPlan | None:
        """El plan activo: el propuesto más reciente o, si no hay, el aceptado."""

    @abstractmethod
    def accept(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Acepta un plan propuesto y descarta el aceptado anterior, en la misma transacción."""

    @abstractmethod
    def discard(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Descarta un plan propuesto o aceptado."""

    @abstractmethod
    def accepted_sessions(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[StudySession]:
        """Sesiones del plan aceptado que empiezan en `[start, end)`, para el calendario (RF-EST-03)."""
