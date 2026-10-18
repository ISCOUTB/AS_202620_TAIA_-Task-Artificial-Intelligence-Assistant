"""Puerto de salida para guardar la memoria corta de cada conversacion."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.ai.domain.conversation import Conversation
from app.modules.ai.domain.messages import PendingAction


class ConversationStore(ABC):
    """Guarda y recupera la conversacion de un estudiante por su id."""

    @abstractmethod
    def get(self, user_id: str) -> Conversation:
        """Devuelve la conversacion; una vacia si no existe."""

    @abstractmethod
    def save(self, conversation: Conversation) -> None:
        ...

    @abstractmethod
    def take_pending(self, user_id: str) -> PendingAction | None:
        """Retira y devuelve la accion pendiente vigente, o None si no hay.

        Debe ser atomica: si dos peticiones la reclaman a la vez, solo una la
        recibe (RF-AGT-04)."""
