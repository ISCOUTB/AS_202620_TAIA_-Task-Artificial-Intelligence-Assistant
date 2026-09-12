"""Pruebas del caso de uso del asistente (sin red ni Gemini)."""

from datetime import datetime, timedelta, timezone

from backend.app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from backend.app.modules.ai.adapters.outbound.in_memory_academic_gateway import (
    InMemoryAcademicGateway,
)
from backend.app.modules.ai.adapters.outbound.in_memory_conversation_store import (
    InMemoryConversationStore,
)
from backend.app.modules.ai.application.dto import NewTask, TaskFilters
from backend.app.modules.ai.application.use_cases.handle_message import (
    HandleUserMessageUseCase,
)
from backend.app.modules.ai.domain.messages import (
    Channel,
    ExtractedFilters,
    ExtractedTaskData,
    IncomingRequest,
    Intent,
    Interpretation,
)

TZ = timezone(timedelta(hours=-5))
DUE = datetime(2026, 9, 20, 20, 0, tzinfo=TZ)


def _msg(text: str, user: str = "u1") -> IncomingRequest:
    return IncomingRequest(user_id=user, text=text, channel=Channel.TELEGRAM)


def _use_case(interpretations, academic=None, store=None, help_answer=None):
    kwargs = {"help_answer": help_answer} if help_answer else {}
    return HandleUserMessageUseCase(
        llm=FakeLLM(interpretations, **kwargs),
        academic=academic or InMemoryAcademicGateway(),
        conversations=store or InMemoryConversationStore(),
        now=lambda: datetime(2026, 9, 10, 12, 0, tzinfo=TZ),
    )


def test_create_task_asks_confirmation_before_writing():
    academic = InMemoryAcademicGateway()
    uc = _use_case(
        [
            Interpretation(
                Intent.CREATE_TASK,
                0.9,
                task=ExtractedTaskData(title="Taller de arquitectura", due_at=DUE),
            )
        ],
        academic=academic,
    )

    reply = uc.execute(_msg("crea la tarea del taller de arquitectura"))

    assert reply.awaiting_confirmation is True
    assert academic.list_tasks("u1", TaskFilters()) == []


def test_create_task_executes_after_yes():
    academic = InMemoryAcademicGateway()
    store = InMemoryConversationStore()
    uc = _use_case(
        [Interpretation(Intent.CREATE_TASK, 0.9, task=ExtractedTaskData(title="Taller", due_at=DUE))],
        academic=academic,
        store=store,
    )

    uc.execute(_msg("crea la tarea taller"))
    reply = uc.execute(_msg("si"))

    tasks = academic.list_tasks("u1", TaskFilters())
    assert "cree la tarea" in reply.text.lower()
    assert len(tasks) == 1 and tasks[0].title == "Taller"


def test_create_task_not_executed_after_no():
    academic = InMemoryAcademicGateway()
    store = InMemoryConversationStore()
    uc = _use_case(
        [Interpretation(Intent.CREATE_TASK, 0.9, task=ExtractedTaskData(title="Taller", due_at=DUE))],
        academic=academic,
        store=store,
    )

    uc.execute(_msg("crea la tarea taller"))
    uc.execute(_msg("no"))

    assert academic.list_tasks("u1", TaskFilters()) == []


def test_low_confidence_does_not_offer_confirmation():
    uc = _use_case(
        [Interpretation(Intent.CREATE_TASK, 0.3, task=ExtractedTaskData(title="algo", due_at=DUE))]
    )

    reply = uc.execute(_msg("mmm no se"))

    assert reply.awaiting_confirmation is False


def test_create_without_title_asks_for_it():
    uc = _use_case(
        [Interpretation(Intent.CREATE_TASK, 0.9, task=ExtractedTaskData(due_at=DUE))]
    )

    reply = uc.execute(_msg("crea una tarea"))

    assert "titulo" in reply.text.lower()


def test_create_without_due_asks_for_it():
    uc = _use_case(
        [Interpretation(Intent.CREATE_TASK, 0.9, task=ExtractedTaskData(title="Leer capitulo 3"))]
    )

    reply = uc.execute(_msg("crea una tarea de leer"))

    assert "fecha" in reply.text.lower()


def test_query_tasks_lists_existing():
    academic = InMemoryAcademicGateway()
    academic.create_task("u1", NewTask(title="Parcial de calculo", due_at=DUE))
    uc = _use_case(
        [Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters())],
        academic=academic,
    )

    reply = uc.execute(_msg("que tengo pendiente"))

    assert "Parcial de calculo" in reply.text


def test_query_tasks_with_text_filter():
    academic = InMemoryAcademicGateway()
    academic.create_task("u1", NewTask(title="Parcial de calculo", due_at=DUE))
    academic.create_task("u1", NewTask(title="Ensayo de historia", due_at=DUE))
    uc = _use_case(
        [Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters(text="calculo"))],
        academic=academic,
    )

    reply = uc.execute(_msg("que tengo de calculo"))

    assert "calculo" in reply.text.lower()
    assert "historia" not in reply.text.lower()


def test_system_help_uses_llm_answer():
    uc = _use_case(
        [Interpretation(Intent.SYSTEM_HELP, 0.9)],
        help_answer="Puedo registrar tareas.",
    )

    reply = uc.execute(_msg("que puedes hacer?"))

    assert reply.text == "Puedo registrar tareas."


def test_unknown_intent_returns_help_text():
    uc = _use_case([Interpretation(Intent.UNKNOWN, 0.9)])

    reply = uc.execute(_msg("hola que tal el clima"))

    assert "tareas" in reply.text.lower()


def test_message_too_long_is_rejected_without_calling_llm():
    llm = FakeLLM([])
    uc = HandleUserMessageUseCase(
        llm=llm,
        academic=InMemoryAcademicGateway(),
        conversations=InMemoryConversationStore(),
    )

    reply = uc.execute(_msg("a" * 1001))

    assert llm.seen == []
    assert "largo" in reply.text.lower()


def test_update_task_resolves_target_and_updates_after_yes():
    academic = InMemoryAcademicGateway()
    academic.create_task("u1", NewTask(title="Ensayo de historia", due_at=DUE))
    store = InMemoryConversationStore()
    new_due = DUE + timedelta(days=1)
    uc = _use_case(
        [
            Interpretation(
                Intent.UPDATE_TASK,
                0.9,
                task=ExtractedTaskData(due_at=new_due),
                task_hint="historia",
            )
        ],
        academic=academic,
        store=store,
    )

    reply = uc.execute(_msg("cambia la entrega del ensayo de historia"))
    assert reply.awaiting_confirmation is True

    reply2 = uc.execute(_msg("si"))
    assert "actualice" in reply2.text.lower()
    assert academic.list_tasks("u1", TaskFilters(text="historia"))[0].due_at == new_due


def test_update_task_ambiguous_target_is_not_confirmed():
    academic = InMemoryAcademicGateway()
    academic.create_task("u1", NewTask(title="Tarea 1 de historia", due_at=DUE))
    academic.create_task("u1", NewTask(title="Tarea 2 de historia", due_at=DUE))
    uc = _use_case(
        [
            Interpretation(
                Intent.UPDATE_TASK,
                0.9,
                task=ExtractedTaskData(due_at=DUE),
                task_hint="historia",
            )
        ],
        academic=academic,
    )

    reply = uc.execute(_msg("cambia la de historia"))

    assert reply.awaiting_confirmation is False
    assert "especifico" in reply.text.lower()


def test_llm_failure_returns_friendly_message():
    uc = HandleUserMessageUseCase(
        llm=FakeLLM([]),  # cola vacia -> LLMError
        academic=InMemoryAcademicGateway(),
        conversations=InMemoryConversationStore(),
        now=lambda: datetime(2026, 9, 10, tzinfo=TZ),
    )

    reply = uc.execute(_msg("crea una tarea"))

    assert "intenta de nuevo" in reply.text.lower()


def test_data_isolation_between_users():
    academic = InMemoryAcademicGateway()
    academic.create_task("u1", NewTask(title="Solo de u1", due_at=DUE))
    uc = _use_case(
        [Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters())],
        academic=academic,
    )

    reply = uc.execute(_msg("mis tareas", user="u2"))

    assert "Solo de u1" not in reply.text
