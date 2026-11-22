"""RF-AGT-15: contexto conversacional acotado, persistido y comun a los dos canales.

Usa el almacen SQL de produccion (`SqlAlchemyConversationStore`) con un reloj
inyectado. `created_at` lo pone PostgreSQL con `now()`, asi que el reloj de la
prueba parte de la hora real y avanza desde ahi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.sqlalchemy_conversation_store import SqlAlchemyConversationStore
from app.modules.ai.application.dto import TaskFilters
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.domain.conversation import Conversation, Turn
from app.modules.ai.domain.messages import (
    COLOMBIA_TZ,
    ActionKind,
    Channel,
    ExtractedTaskData,
    IncomingRequest,
    Intent,
    Interpretation,
    PendingAction,
)

DUE = datetime(2026, 12, 4, 23, 59, tzinfo=COLOMBIA_TZ)


def _store(session_factory, minutes_later: float = 0) -> SqlAlchemyConversationStore:
    """Un almacen nuevo equivale a un reinicio del servidor."""
    moment = datetime.now(timezone.utc) + timedelta(minutes=minutes_later)
    return SqlAlchemyConversationStore(session_factory, now=lambda: moment)


def _save_turns(store: SqlAlchemyConversationStore, user_id: str, *texts: str) -> None:
    conversation = store.get(user_id)
    for index, text in enumerate(texts):
        conversation.record("user" if index % 2 == 0 else "assistant", text)
    store.save(conversation)


def _pending(subject_id: str | None = None) -> PendingAction:
    return PendingAction(
        kind=ActionKind.CREATE_TASK,
        task=ExtractedTaskData(
            title="Informe de laboratorio",
            due_at=DUE,
            subject="Física",
            type="exam",
            title_generated=True,
        ),
        summary="Voy a crear... Confirmas? (si / no)",
        subject_id=subject_id,
    )


def test_context_survives_a_restart_rf_agt_15(clean_db):
    user_id = str(uuid.uuid4())
    _save_turns(_store(clean_db), user_id, "hola", "hola, en que te ayudo?")

    restored = _store(clean_db).get(user_id)

    assert [turn.text for turn in restored.turns] == ["hola", "hola, en que te ayudo?"]


def test_context_expires_after_thirty_minutes_of_inactivity_rf_agt_15(clean_db):
    user_id = str(uuid.uuid4())
    _save_turns(_store(clean_db), user_id, "hola", "hola, en que te ayudo?")

    assert len(_store(clean_db, minutes_later=29).get(user_id).turns) == 2
    assert _store(clean_db, minutes_later=31).get(user_id).turns == []


def test_a_new_message_restarts_the_inactivity_window_rf_agt_15(clean_db):
    """Vence por inactividad, no por una ventana fija (diccionario de datos 8.2)."""
    user_id = str(uuid.uuid4())
    _save_turns(_store(clean_db), user_id, "primero")
    later = _store(clean_db, minutes_later=20)
    _save_turns(later, user_id, "segundo")
    # PostgreSQL fecha el segundo mensaje con su hora real: se adelanta para simular los 20 minutos.
    with clean_db.begin() as session:
        session.execute(
            text("UPDATE conversation_messages SET created_at = created_at + interval '20 minutes' WHERE content = 'segundo'")
        )

    turns = _store(clean_db, minutes_later=45).get(user_id).turns

    assert [turn.text for turn in turns] == ["primero", "segundo"]


def test_context_keeps_the_last_ten_messages_rf_agt_15(clean_db):
    user_id = str(uuid.uuid4())
    _save_turns(_store(clean_db), user_id, *[f"mensaje {n}" for n in range(12)])

    turns = _store(clean_db).get(user_id).turns

    assert [turn.text for turn in turns] == [f"mensaje {n}" for n in range(2, 12)]


def test_context_is_cut_to_four_thousand_characters_on_load_rf_agt_15(clean_db):
    user_id = str(uuid.uuid4())
    _save_turns(_store(clean_db), user_id, "a" * 1500, "b" * 1500, "c" * 1500)

    turns = _store(clean_db).get(user_id).turns

    assert [turn.text[0] for turn in turns] == ["b", "c"]


def test_restored_conversation_is_trimmed_by_the_domain_rf_agt_15():
    turns = [Turn("user", f"m{n}") for n in range(12)] + [Turn("assistant", "x" * 3990)]

    conversation = Conversation(user_id="u1", turns=turns)

    assert sum(len(turn.text) for turn in conversation.turns) <= 4000
    assert conversation.turns[-1].text == "x" * 3990


def test_pending_action_round_trips_with_backend_ids_rf_agt_15(clean_db):
    user_id = str(uuid.uuid4())
    subject_id = str(uuid.uuid4())
    store = _store(clean_db)
    conversation = store.get(user_id)
    conversation.set_pending(_pending(subject_id))
    store.save(conversation)

    pending = _store(clean_db, minutes_later=1).get(user_id).pending

    assert pending == _pending(subject_id)


def test_pending_action_expires_after_ten_minutes_rf_agt_04(clean_db):
    user_id = str(uuid.uuid4())
    store = _store(clean_db)
    conversation = store.get(user_id)
    conversation.set_pending(_pending())
    store.save(conversation)

    assert _store(clean_db, minutes_later=9).get(user_id).pending is not None
    late = _store(clean_db, minutes_later=11)
    assert late.get(user_id).pending is None
    assert late.take_pending(user_id) is None


def test_context_is_shared_by_the_app_and_telegram_rf_agt_15(clean_db):
    """La accion propuesta en la app se confirma desde Telegram: el contexto es por usuario."""
    user_id = str(uuid.uuid4())
    academic = InMemoryAcademicGateway()
    academic.add_subject(user_id, "Física")
    llm = FakeLLM([
        Interpretation(
            Intent.CREATE_TASK,
            0.9,
            task=ExtractedTaskData(title="Informe", due_at=DUE, subject="fisica"),
        )
    ])

    def use_case() -> HandleUserMessageUseCase:
        return HandleUserMessageUseCase(llm=llm, academic=academic, conversations=_store(clean_db))

    use_case().execute(IncomingRequest(user_id, "crea el informe de fisica", Channel.APP))
    reply = use_case().execute(IncomingRequest(user_id, "si", Channel.TELEGRAM))

    assert reply.text.startswith('Listo, cree la tarea "Informe"')
    assert [task.title for task in academic.list_tasks(user_id, TaskFilters())] == ["Informe"]
    assert len(llm.seen) == 1
