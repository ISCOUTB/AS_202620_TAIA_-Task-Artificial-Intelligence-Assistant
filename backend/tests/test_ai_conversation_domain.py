"""Pruebas del dominio de conversacion del modulo de IA."""

from backend.app.modules.ai.domain.conversation import Conversation
from backend.app.modules.ai.domain.messages import (
    HISTORY_LIMIT,
    ActionKind,
    ExtractedTaskData,
    PendingAction,
)


def test_conversation_keeps_only_recent_turns():
    convo = Conversation(user_id="u1")

    for i in range(HISTORY_LIMIT + 5):
        convo.record("user", f"m{i}")

    assert len(convo.turns) == HISTORY_LIMIT
    assert convo.turns[-1].text == f"m{HISTORY_LIMIT + 4}"


def test_conversation_trims_by_size():
    convo = Conversation(user_id="u1")

    convo.record("user", "a" * 3000)
    convo.record("user", "b" * 3000)

    assert len(convo.turns) == 1
    assert convo.turns[0].text.startswith("b")


def test_pending_action_set_and_clear():
    convo = Conversation(user_id="u1")
    action = PendingAction(
        kind=ActionKind.CREATE_TASK,
        task=ExtractedTaskData(title="x"),
        summary="confirmas?",
    )

    convo.set_pending(action)
    assert convo.pending is action

    convo.clear_pending()
    assert convo.pending is None
