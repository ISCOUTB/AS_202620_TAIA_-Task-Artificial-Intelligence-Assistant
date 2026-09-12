"""ConversationStore en memoria. No persiste entre reinicios."""

from __future__ import annotations

from backend.app.modules.ai.application.ports.conversation_store import ConversationStore
from backend.app.modules.ai.domain.conversation import Conversation


class InMemoryConversationStore(ConversationStore):
    def __init__(self) -> None:
        self._by_user: dict[str, Conversation] = {}

    def get(self, user_id: str) -> Conversation:
        return self._by_user.get(user_id) or Conversation(user_id=user_id)

    def save(self, conversation: Conversation) -> None:
        self._by_user[conversation.user_id] = conversation
