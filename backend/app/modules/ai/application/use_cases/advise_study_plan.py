"""RF-EST-02 · El LLM sugiere qué actividad estudiar en cada hueco libre."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from app.modules.ai.application.ports.inbound.study_plan_advisor import ItemOption, SlotOption
from app.modules.ai.application.ports.llm import LLMError, LLMPort

logger = logging.getLogger("taia.ai")


class AdviseStudyPlanUseCase:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def propose(self, slots: Sequence[SlotOption], items: Sequence[ItemOption]) -> list[tuple[int, int]]:
        """Una sola llamada al LLM. Si falla, Academic arma el plan con sus reglas (RF-AGT-20)."""

        if not slots or not items:
            return []
        try:
            pairs = self._llm.propose_study_sessions(slots, items)
        except LLMError as error:
            logger.warning("study_plan_llm_failed", extra={"fields": {"error": type(error).__name__}})
            return []
        slot_ids = {slot.index for slot in slots}
        item_ids = {item.index for item in items}
        # Índices inventados por el modelo se descartan (RF-AGT-17).
        return [(item, slot) for item, slot in pairs if item in item_ids and slot in slot_ids]
