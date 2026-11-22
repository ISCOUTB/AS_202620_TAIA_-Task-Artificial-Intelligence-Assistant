"""Puerto hacia quien sugiere qué actividad va en cada hueco (RF-EST-02).

Lo implementa un adaptador que llama al puerto que publica el módulo AI. Recibe
solo los huecos y las actividades numeradas, sin identificadores (RF-AGT-17).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.modules.academic.application.study_planner import FreeSlot, PlanItem


class StudySessionAdvisor(Protocol):
    def propose(self, slots: Sequence[FreeSlot], items: Sequence[PlanItem]) -> list[tuple[int, int]]:
        """Pares (actividad, hueco). Si no puede sugerir, devuelve una lista vacía."""
        ...
