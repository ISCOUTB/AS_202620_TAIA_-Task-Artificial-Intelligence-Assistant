"""Pide a AI la sugerencia del plan mediante el puerto que AI publica (RF-EST-02).

Solo viajan los huecos y las actividades numerados: ni el usuario ni los
identificadores de las actividades salen de Academic (RF-AGT-17).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.modules.academic.application.study_planner import FreeSlot, PlanItem
from app.modules.ai.application.ports.inbound.study_plan_advisor import (
    ItemOption,
    SlotOption,
    get_study_plan_advisor,
)


class AiStudySessionAdvisor:
    def propose(self, slots: Sequence[FreeSlot], items: Sequence[PlanItem]) -> list[tuple[int, int]]:
        return get_study_plan_advisor().propose(
            [SlotOption(slot.index, slot.starts_at, slot.ends_at) for slot in slots],
            [
                ItemOption(item.index, item.title, item.subject_name, item.due_at, item.priority, item.sessions)
                for item in items
            ],
        )
