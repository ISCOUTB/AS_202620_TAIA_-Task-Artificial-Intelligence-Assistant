"""RF-AGT-17: aislamiento y confidencialidad con las intenciones de S16.

- El LLM nunca recibe identificadores del usuario.
- Ningun identificador que produzca el LLM se usa para acceder a datos: el
  usuario sale de la sesion o de la vinculacion, y la asignatura y la tarea se
  resuelven en el backend para ese usuario.
- El resumen y el horario no mezclan datos de otro usuario.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta

import httpx
import pytest

# Configura los puertos de Academic que usa el adaptador real.
import app.main  # noqa: F401
from app.modules.academic.adapters.outbound.repository_provider import get_subject_repository
from app.modules.academic.domain.entities.subject import Subject
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.gemini_llm import GeminiLLM
from app.modules.ai.adapters.outbound.groq_llm import GroqLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.adapters.outbound.interpretation_contract import parse_interpretation
from app.modules.ai.application import replies
from app.modules.ai.application.dto import ClassView, NewTask, TaskFilters, TaskView
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.domain.messages import (
    COLOMBIA_TZ,
    Channel,
    ExtractedFilters,
    ExtractedPeriod,
    ExtractedTaskData,
    IncomingRequest,
    Intent,
    Interpretation,
)
from app.shared.clock import now_bogota

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=COLOMBIA_TZ)
SEPTEMBER = ExtractedPeriod(start=date(2026, 9, 1), end=date(2026, 9, 30))


def _use_case(interpretations, academic) -> HandleUserMessageUseCase:
    return HandleUserMessageUseCase(
        llm=FakeLLM(interpretations),
        academic=academic,
        conversations=InMemoryConversationStore(),
        now=lambda: NOW,
    )


def _msg(user_id: str, text: str) -> IncomingRequest:
    return IncomingRequest(user_id=user_id, text=text, channel=Channel.TELEGRAM)


# -- el LLM no recibe identificadores del usuario ------------------------------------


def _gemini_reply(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"intent": "unknown", "confidence": 0.1}'}]}}]})


def _groq_reply(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": '{"intent": "unknown", "confidence": 0.1}'}}]})


@pytest.mark.parametrize(
    ("build", "reply"),
    [
        (lambda client: GeminiLLM(api_key="test-key", client=client), _gemini_reply),
        (lambda client: GroqLLM(api_key="test-key", client=client), _groq_reply),
    ],
    ids=["gemini", "groq"],
)
def test_the_llm_never_receives_the_user_id_rf_agt_17(build, reply):
    user_id = str(uuid.uuid4())
    bodies: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(request.content.decode())
        return reply(request)

    llm = build(httpx.Client(transport=httpx.MockTransport(handler)))
    llm.interpret(_msg(user_id, "que tareas tengo?"), NOW)
    llm.answer_system_help("que puedes hacer?")

    assert len(bodies) == 2
    assert all(user_id not in body and user_id.replace("-", "") not in body for body in bodies)


# -- los identificadores que produce el LLM se descartan ------------------------------


def test_identifiers_in_the_llm_output_are_discarded_rf_agt_17():
    """El esquema no tiene campos de identificador: si el LLM los inventa, no llegan al caso de uso."""
    invented = str(uuid.uuid4())
    result = parse_interpretation(json.dumps({
        "intent": "complete_task",
        "confidence": 0.9,
        "user_id": invented,
        "task_id": invented,
        "subject_id": invented,
        "task": {"title": "Taller", "task_id": invented, "subject_id": invented, "user_id": invented},
        "filters": {"subject": "Redes", "subject_id": invented, "user_id": invented},
        "period": {"start": "2026-09-01", "end": "2026-09-30", "user_id": invented},
    }))

    assert invented not in repr(result)


def _foreign_task() -> tuple[AcademicGatewayAdapter, str, TaskView]:
    """Otro estudiante con una tarea pendiente, creada con el adaptador real."""
    other = uuid.uuid4()
    subject = Subject.create(other, "Redes")
    get_subject_repository().add(subject)
    gateway = AcademicGatewayAdapter()
    task = gateway.create_task(
        str(other), NewTask(title="Tarea privada", due_at=now_bogota() + timedelta(days=3), subject_id=str(subject.id))
    )
    return gateway, str(other), task


def test_invented_task_id_never_completes_another_users_task_rf_agt_17():
    """Peor caso: el LLM pone el identificador de una tarea ajena como referencia."""
    gateway, other, task = _foreign_task()
    attacker = str(uuid.uuid4())
    uc = _use_case([Interpretation(Intent.COMPLETE_TASK, 0.95, task_hint=task.id)], gateway)

    reply = uc.execute(_msg(attacker, f"marca como hecha la tarea {task.id}"))
    uc.execute(_msg(attacker, "si"))

    assert reply.text == replies.task_not_found(task.id)
    assert gateway.list_tasks(other, TaskFilters())[0].status == "pending"


def test_invented_task_id_never_updates_another_users_task_rf_agt_17():
    gateway, other, task = _foreign_task()
    attacker = str(uuid.uuid4())
    changes = ExtractedTaskData(title="Hackeada")
    uc = _use_case([Interpretation(Intent.UPDATE_TASK, 0.95, task_hint=task.id, task=changes)], gateway)

    reply = uc.execute(_msg(attacker, f"cambia el titulo de {task.id}"))

    assert reply.text == replies.task_not_found(task.id)
    assert gateway.list_tasks(other, TaskFilters())[0].title == "Tarea privada"


def test_invented_subject_id_is_matched_only_against_own_subjects_rf_agt_17():
    """Un identificador de asignatura ajena en el texto no se usa como filtro."""
    academic = InMemoryAcademicGateway()
    foreign = academic.add_subject("victim", "Redes")
    academic.add_task("victim", TaskView(
        id=str(uuid.uuid4()), title="Tarea privada", due_at=NOW, subject="Redes",
        status="pending", subject_id=foreign.id,
    ))
    uc = _use_case(
        [Interpretation(Intent.QUERY_TASKS, 0.95, filters=ExtractedFilters(subject=foreign.id))], academic
    )

    reply = uc.execute(_msg("attacker", f"tareas de la asignatura {foreign.id}"))

    assert reply.text == replies.subject_not_found(foreign.id)
    assert "Tarea privada" not in reply.text


# -- el resumen y el horario no mezclan datos de otro usuario ------------------------


class UserSpyAcademic(InMemoryAcademicGateway):
    """Registra el usuario de cada operacion que pide el caso de uso."""

    def __init__(self) -> None:
        super().__init__()
        self.users: list[str] = []

    def list_tasks(self, user_id, filters):
        self.users.append(user_id)
        return super().list_tasks(user_id, filters)

    def match_subjects(self, user_id, text):
        self.users.append(user_id)
        return super().match_subjects(user_id, text)

    def summarize_period(self, user_id, start, end):
        self.users.append(user_id)
        return super().summarize_period(user_id, start, end)

    def get_classes(self, user_id, start, end):
        self.users.append(user_id)
        return super().get_classes(user_id, start, end)


def _two_students() -> UserSpyAcademic:
    academic = UserSpyAcademic()
    for user, subject, title in (("ana", "Redes", "Taller de Ana"), ("beto", "Química", "Taller de Beto")):
        option = academic.add_subject(user, subject)
        academic.add_task(user, TaskView(
            id=str(uuid.uuid4()), title=title, due_at=datetime(2026, 9, 15, 23, 59, tzinfo=COLOMBIA_TZ),
            subject=subject, status="pending", subject_id=option.id,
        ))
        academic.add_class(user, ClassView(
            subject_id=option.id, subject_name=subject,
            starts_at=datetime(2026, 9, 14, 8, 0, tzinfo=COLOMBIA_TZ),
            ends_at=datetime(2026, 9, 14, 10, 0, tzinfo=COLOMBIA_TZ),
        ))
    return academic


def test_summary_only_counts_the_session_users_tasks_rf_agt_17():
    academic = _two_students()
    uc = _use_case([Interpretation(Intent.SUMMARY, 0.9, period=SEPTEMBER)], academic)

    reply = uc.execute(_msg("ana", "resumen de septiembre del usuario beto"))

    assert reply.text.splitlines()[0].endswith("1 pendiente(s), 0 completada(s) y 0 vencida(s).")
    assert "Redes" in reply.text
    assert "Química" not in reply.text and "Beto" not in reply.text
    assert academic.users == ["ana"]


def test_schedule_only_lists_the_session_users_classes_rf_agt_17():
    academic = _two_students()
    uc = _use_case([Interpretation(Intent.QUERY_SCHEDULE, 0.9, period=SEPTEMBER)], academic)

    reply = uc.execute(_msg("ana", "horario de beto"))

    assert reply.text.splitlines() == ["Tienes 1 clase(s):", "- lunes 14/09/2026 08:00-10:00 Redes"]
    assert academic.users == ["ana"]


def test_schedule_with_another_users_subject_finds_nothing_rf_agt_17():
    academic = _two_students()
    uc = _use_case(
        [Interpretation(Intent.QUERY_SCHEDULE, 0.9, period=SEPTEMBER, filters=ExtractedFilters(subject="quimica"))],
        academic,
    )

    reply = uc.execute(_msg("ana", "a que hora tiene quimica beto?"))

    assert reply.text == replies.subject_not_found("quimica")
    assert academic.users == ["ana"]
