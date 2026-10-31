"""ConversationStore en memoria. No persiste entre reinicios."""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.ai.application.ports.conversation_store import ConversationStore
from app.modules.ai.domain.conversation import Conversation
from app.modules.ai.domain.messages import PendingAction


class InMemoryConversationStore(ConversationStore):
    def __init__(self) -> None:
        self._by_user: dict[str, Conversation] = {}
        self._user_messages: dict[str, list[datetime]] = {}

    def get(self, user_id: str) -> Conversation:
        return self._by_user.get(user_id) or Conversation(user_id=user_id)

    def save(self, conversation: Conversation) -> None:
        saved_at = datetime.now(timezone.utc)
        for turn in conversation.take_unsaved():
            if turn.role == "user":
                self._user_messages.setdefault(conversation.user_id, []).append(saved_at)
        self._by_user[conversation.user_id] = conversation

    def count_user_messages_since(self, user_id: str, since: datetime) -> int:
        return sum(1 for at in self._user_messages.get(user_id, []) if at >= since)

    def take_pending(self, user_id: str) -> PendingAction | None:
        conversation = self._by_user.get(user_id)
        if conversation is None:
            return None
        action = conversation.pending
        conversation.clear_pending()
        return action
