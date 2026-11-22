"""Puerto de entrada de AI que sugiere qué actividad va en cada hueco del plan (RF-EST-02).

Academic calcula los huecos y valida las reglas; AI solo sugiere. Recibe datos
numerados, sin identificadores de usuario ni de actividades (RF-AGT-17), y
nunca falla: si el LLM no responde, devuelve una lista vacía (RF-AGT-20).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SlotOption:
    index: int
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class ItemOption:
    index: int
    title: str
    subject_name: str
    due_at: datetime
    priority: str | None
    sessions: int


class StudyPlanAdvisor(Protocol):
    def propose(self, slots: Sequence[SlotOption], items: Sequence[ItemOption]) -> list[tuple[int, int]]:
        """Pares (actividad, hueco) sugeridos; lista vacía si no hay sugerencia."""
        ...


_service: StudyPlanAdvisor | None = None


def configure_study_plan_advisor(service: StudyPlanAdvisor) -> None:
    global _service
    _service = service


def get_study_plan_advisor() -> StudyPlanAdvisor:
    if _service is None:
        raise RuntimeError("El asesor del plan de estudio no está configurado.")
    return _service
