"""Puerto de salida para guardar la memoria corta de cada conversacion."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.modules.ai.domain.conversation import Conversation


class ConversationStore(ABC):
    """Guarda y recupera la conversacion de un estudiante por su id."""

    @abstractmethod
    def get(self, user_id: str) -> Conversation:
        """Devuelve la conversacion; una vacia si no existe."""

    @abstractmethod
    def save(self, conversation: Conversation) -> None:
        ...
