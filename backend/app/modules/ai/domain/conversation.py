"""Memoria corta de una conversacion con un estudiante."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.ai.domain.messages import (
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

    El adaptador configurado conserva este estado entre reinicios."""

    user_id: str
    turns: list[Turn] = field(default_factory=list)
    pending: PendingAction | None = None
    # Mensajes registrados que el adaptador todavia no guardo. El adaptador solo
    # agrega estos, asi que los anteriores conservan su fecha (RF-AGT-19).
    unsaved: list[Turn] = field(default_factory=list, repr=False, compare=False)

    def record(self, role: str, text: str) -> None:
        """Agrega un mensaje y descarta los mas antiguos pasado el limite."""

        turn = Turn(role=role, text=text)
        self.turns.append(turn)
        self.unsaved.append(turn)
        while len(self.turns) > 1 and (
            len(self.turns) > HISTORY_LIMIT or self._size() > MAX_HISTORY_CHARS
        ):
            self.turns.pop(0)

    def take_unsaved(self) -> list[Turn]:
        """Entrega los mensajes pendientes de guardar y los marca como guardados."""

        turns, self.unsaved = self.unsaved, []
        return turns

    def set_pending(self, action: PendingAction) -> None:
        self.pending = action

    def clear_pending(self) -> None:
        self.pending = None

    def _size(self) -> int:
        return sum(len(turn.text) for turn in self.turns)
