"""Memoria corta de una conversacion con un estudiante."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.modules.ai.domain.messages import (
    HISTORY_LIMIT,
    MAX_HISTORY_CHARS,
    PendingAction,
)


@dataclass(frozen=True)
class Turn:
    """Un mensaje dentro de la conversacion."""

    role: str  # "user" o "assistant"
    text: str


@dataclass
class Conversation:
    """Ultimos mensajes con un estudiante y la accion pendiente de confirmar.

    No se persiste entre reinicios en esta version (ver context_IA.md)."""

    user_id: str
    turns: list[Turn] = field(default_factory=list)
    pending: PendingAction | None = None

    def record(self, role: str, text: str) -> None:
        """Agrega un mensaje y descarta los mas antiguos pasado el limite."""

        self.turns.append(Turn(role=role, text=text))
        while len(self.turns) > 1 and (
            len(self.turns) > HISTORY_LIMIT or self._size() > MAX_HISTORY_CHARS
        ):
            self.turns.pop(0)

    def set_pending(self, action: PendingAction) -> None:
        self.pending = action

    def clear_pending(self) -> None:
        self.pending = None

    def _size(self) -> int:
        return sum(len(turn.text) for turn in self.turns)
