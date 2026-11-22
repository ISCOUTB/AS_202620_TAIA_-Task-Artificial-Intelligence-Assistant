"""Pruebas del caso de uso del agente para las intenciones de S16 (D1 a D6).

Cada prueba cita el requerimiento que cubre. El LLM es un doble (`FakeLLM`): no
sale a la red. Academic es el doble en memoria, salvo en el criterio de
RF-AGT-10, que usa el adaptador real con un doble de `AcademicInsights`.
"""

from __future__ import annotations

import unicodedata
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

# Configura los puertos de Academic que usa el adaptador real del criterio de RF-AGT-10.
import app.main  # noqa: F401
from app.modules.academic.adapters.outbound.repository_provider import get_subject_repository
from app.modules.academic.application.ports.inbound.task_management import AcademicSubjectRef
from app.modules.academic.domain.entities.subject import Subject
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.application import replies
from app.modules.ai.application.dto import ClassView, NewTask, TaskFilters, TaskView
from app.modules.ai.application.ports.llm import LLMUsage
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

# Jueves 10 de septiembre de 2026, mediodia en Colombia.
NOW = datetime(2026, 9, 10, 12, 0, tzinfo=COLOMBIA_TZ)
DUE = datetime(2026, 9, 20, 20, 0, tzinfo=COLOMBIA_TZ)
USER = "u1"


def _msg(text: str, user: str = USER, channel: Channel = Channel.APP) -> IncomingRequest:
    return IncomingRequest(user_id=user, text=text, channel=channel)


def _use_case(interpretations, academic=None, store=None, llm=None):
    return HandleUserMessageUseCase(
        llm=llm or FakeLLM(interpretations),
        academic=academic or InMemoryAcademicGateway(),
        conversations=store or InMemoryConversationStore(),
        now=lambda: NOW,
    )


def _create(**task) -> Interpretation:
    return Interpretation(Intent.CREATE_TASK, 0.9, task=ExtractedTaskData(**task))


def _task(title: str, due: datetime, **extra) -> TaskView:
    fields = {"subject": None, "status": "pending"} | extra
    return TaskView(id=str(uuid.uuid4()), title=title, due_at=due, **fields)


# -- D1 · RF-AGT-10 y RF-AGT-05: asignatura, tipo y fecha ----------------------


class PrefixInsights:
    """Doble de `AcademicInsights.match_subjects`: sin tildes ni mayusculas y por prefijos.

    El resumen y el horario no se usan en estas pruebas."""

    def __init__(self, subjects: list[AcademicSubjectRef]) -> None:
        self._subjects = subjects
        self.calls: list[tuple[uuid.UUID, str]] = []

    def match_subjects(self, user_id, text, limit=5):
        self.calls.append((user_id, text))
        wanted = _words(text)
        return [s for s in self._subjects if _prefixes(wanted, _words(s.name))][:limit]


def _words(text: str) -> list[str]:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold().split()


def _prefixes(wanted: list[str], words: list[str]) -> bool:
    return len(wanted) <= len(words) and all(w.startswith(p) for p, w in zip(wanted, words))


def test_criterion_tasks_in_matematicas_basicas_rf_agt_10():
    """RF-AGT-10: "¿Qué tareas tengo en matematicas basicas?" devuelve las de "Matemáticas Básicas"."""
    owner = uuid.uuid4()
    math = Subject.create(owner, "Matemáticas Básicas")
    physics = Subject.create(owner, "Física")
    get_subject_repository().add(math)
    get_subject_repository().add(physics)
    insights = PrefixInsights(
        [AcademicSubjectRef(math.id, math.name), AcademicSubjectRef(physics.id, physics.name)]
    )
    academic = AcademicGatewayAdapter(insights=insights)
    due = now_bogota() + timedelta(days=3)
    academic.create_task(str(owner), NewTask(title="Taller de derivadas", due_at=due, subject_id=str(math.id)))
    academic.create_task(str(owner), NewTask(title="Informe de laboratorio", due_at=due, subject_id=str(physics.id)))
    llm = FakeLLM([
        Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters(subject="matematicas basicas"))
    ])

    reply = _use_case(None, academic=academic, llm=llm).execute(
        _msg("¿Qué tareas tengo en matematicas basicas?", user=str(owner))
    )

    assert "Taller de derivadas" in reply.text
    assert "Matemáticas Básicas" in reply.text
    assert "Informe de laboratorio" not in reply.text
    # La coincidencia la hace Academic con el texto que extrajo el LLM, para el usuario de la sesion.
    assert insights.calls == [(owner, "matematicas basicas")]


def test_create_with_one_matching_subject_uses_its_id_rf_agt_10():
    academic = InMemoryAcademicGateway()
    subject = academic.add_subject(USER, "Matemáticas Básicas")
    uc = _use_case([_create(title="Taller", due_at=DUE, subject="matematicas")], academic=academic)

    proposal = uc.execute(_msg("crea el taller de matematicas"))
    uc.execute(_msg("si"))

    assert proposal.awaiting_confirmation is True
    assert "de Matemáticas Básicas" in proposal.text
    [created] = academic.list_tasks(USER, TaskFilters())
    assert created.subject_id == subject.id


def test_create_with_several_subjects_lists_five_and_saves_nothing_rf_agt_05():
    """RF-AGT-05: con varias candidatas pregunta con hasta 5 opciones y no guarda la solicitud."""
    academic = InMemoryAcademicGateway()
    names = [f"Física {n}" for n in ("I", "II", "III", "IV", "V", "VI")]
    for name in names:
        academic.add_subject(USER, name)
    store = InMemoryConversationStore()
    llm = FakeLLM([
        _create(title="Taller", due_at=DUE, subject="fisica"),
        Interpretation(Intent.UNKNOWN, 0.9),
    ])
    uc = _use_case(None, academic=academic, store=store, llm=llm)

    reply = uc.execute(_msg("crea el taller de fisica"))

    assert reply.awaiting_confirmation is False
    assert all(name in reply.text for name in names[:5])
    assert "Física VI" not in reply.text
    assert "Escribe de nuevo la solicitud" in reply.text
    assert store.get(USER).pending is None
    # Un "si" despues no crea nada: no habia solicitud guardada.
    uc.execute(_msg("si"))
    assert academic.list_tasks(USER, TaskFilters()) == []


def test_create_with_no_matching_subject_asks_and_saves_nothing_rf_agt_05():
    academic = InMemoryAcademicGateway()
    academic.add_subject(USER, "Redes")
    store = InMemoryConversationStore()
    uc = _use_case([_create(title="Taller", due_at=DUE, subject="quimica")], academic=academic, store=store)

    reply = uc.execute(_msg("crea el taller de quimica"))

    assert reply.text == replies.subject_not_found("quimica")
    assert reply.awaiting_confirmation is False
    assert store.get(USER).pending is None


def test_create_without_subject_asks_for_it_rf_agt_05():
    uc = _use_case([_create(title="Taller", due_at=DUE)])

    reply = uc.execute(_msg("crea un taller para el viernes"))

    assert reply.text == replies.missing_subject()
    assert reply.awaiting_confirmation is False


def test_create_without_due_date_asks_for_it_rf_agt_05():
    academic = InMemoryAcademicGateway()
    academic.add_subject(USER, "Redes")
    uc = _use_case([_create(title="Taller", subject="redes")], academic=academic)

    reply = uc.execute(_msg("crea el taller de redes"))

    assert reply.text == replies.missing_due()
    assert reply.awaiting_confirmation is False


def test_create_exam_keeps_its_type_rf_agt_05():
    academic = InMemoryAcademicGateway()
    academic.add_subject(USER, "Redes")
    uc = _use_case([_create(title="Parcial 1", due_at=DUE, subject="redes", type="exam")], academic=academic)

    proposal = uc.execute(_msg("tengo parcial de redes el 20"))
    uc.execute(_msg("si"))

    assert proposal.text.startswith('Voy a crear el examen "Parcial 1"')
    assert [task.type for task in academic.list_tasks(USER, TaskFilters())] == ["exam"]


def test_create_without_type_is_a_task_rf_agt_05():
    academic = InMemoryAcademicGateway()
    academic.add_subject(USER, "Redes")
    uc = _use_case([_create(title="Taller", due_at=DUE, subject="redes")], academic=academic)

    proposal = uc.execute(_msg("crea el taller de redes"))
    uc.execute(_msg("si"))

    assert proposal.text.startswith('Voy a crear la tarea "Taller"')
    assert [task.type for task in academic.list_tasks(USER, TaskFilters())] == ["task"]


def test_create_proposal_uses_a_single_llm_call_rf_agt_05():
    academic = InMemoryAcademicGateway()
    academic.add_subject(USER, "Redes")
    llm = FakeLLM([_create(title="Taller", due_at=DUE, subject="redes")])
    uc = _use_case(None, academic=academic, llm=llm)

    uc.execute(_msg("crea el taller de redes"))
    uc.execute(_msg("si"))

    assert llm.seen == ["crea el taller de redes"]


# -- D2 · RF-AGT-06 y RF-AGT-07: titulo generado y recordatorios por defecto ----


def test_criterion_lab_report_gets_a_generated_title_rf_agt_06_rf_agt_07():
    """RF-AGT-06: "Tengo que entregar el informe de laboratorio de física el viernes" genera
    un titulo y lo asocia a Física sin pedirlo. RF-AGT-07: la confirmacion dice que se
    aplican los recordatorios por defecto."""
    academic = InMemoryAcademicGateway()
    physics = academic.add_subject(USER, "Física")
    friday = datetime(2026, 9, 11, 23, 59, tzinfo=COLOMBIA_TZ)
    llm = FakeLLM([
        _create(title="Informe de laboratorio", title_generated=True, due_at=friday, subject="física")
    ])
    uc = _use_case(None, academic=academic, llm=llm)

    proposal = uc.execute(_msg("Tengo que entregar el informe de laboratorio de física el viernes"))

    assert proposal.awaiting_confirmation is True
    assert proposal.text == (
        'Voy a crear la tarea "Informe de laboratorio" de Física para el 11/09/2026 23:59, '
        "con recordatorios cada 2 dias y la tarde anterior. Confirmas? (si / no)"
    )
    uc.execute(_msg("sí"))
    [created] = academic.list_tasks(USER, TaskFilters())
    assert (created.title, created.subject_id) == ("Informe de laboratorio", physics.id)
    # El titulo salio de la misma llamada de interpretacion.
    assert len(llm.seen) == 1


def test_rejecting_the_generated_title_creates_nothing_rf_agt_06():
    academic = InMemoryAcademicGateway()
    academic.add_subject(USER, "Física")
    uc = _use_case(
        [_create(title="Informe de laboratorio", title_generated=True, due_at=DUE, subject="fisica")],
        academic=academic,
    )

    uc.execute(_msg("tengo que entregar el informe de fisica"))
    reply = uc.execute(_msg("no"))

    assert reply.text == replies.cancelled()
    assert academic.list_tasks(USER, TaskFilters()) == []


# -- D3 · RF-AGT-02, 08 y 09: completar, actualizar y fuera de la lista --------


def _complete(hint: str, confidence: float = 0.9) -> Interpretation:
    return Interpretation(Intent.COMPLETE_TASK, confidence, task_hint=hint)


def test_complete_task_asks_confirmation_and_completes_after_yes_rf_agt_09():
    academic = InMemoryAcademicGateway()
    target = academic.add_task(USER, _task("Taller de física", DUE, subject="Física"))
    llm = FakeLLM([_complete("taller de física")])
    uc = _use_case(None, academic=academic, llm=llm)

    proposal = uc.execute(_msg("ya entregué el taller de física"))
    assert academic.list_tasks(USER, TaskFilters())[0].status == "pending"
    done = uc.execute(_msg("si"))

    assert proposal.awaiting_confirmation is True
    assert proposal.text == 'Voy a marcar como completada la tarea "Taller de física" (Física). Confirmas? (si / no)'
    assert done.text == 'Listo, marque como completada la tarea "Taller de física".'
    assert academic.list_tasks(USER, TaskFilters())[0].id == target.id
    assert academic.list_tasks(USER, TaskFilters())[0].status == "completed"
    # La confirmacion se evalua sin llamar al LLM (RF-AGT-04).
    assert len(llm.seen) == 1


@pytest.mark.parametrize("answer", ["no", "pues la verdad hice la mitad y no se si cuenta"])
def test_complete_task_is_cancelled_without_a_clear_yes_rf_agt_09(answer):
    academic = InMemoryAcademicGateway()
    academic.add_task(USER, _task("Taller de física", DUE))
    llm = FakeLLM([_complete("taller de física")])
    uc = _use_case(None, academic=academic, llm=llm)

    uc.execute(_msg("ya entregué el taller de física"))
    uc.execute(_msg(answer))

    assert academic.list_tasks(USER, TaskFilters())[0].status == "pending"
    assert len(llm.seen) == 1


def test_complete_task_with_several_candidates_lists_five_and_does_not_choose_rf_agt_09():
    academic = InMemoryAcademicGateway()
    for day in range(7):
        academic.add_task(USER, _task(f"Taller {day + 1}", DUE + timedelta(days=day)))
    store = InMemoryConversationStore()
    uc = _use_case([_complete("taller")], academic=academic, store=store)

    reply = uc.execute(_msg("ya entregue el taller"))

    assert reply.awaiting_confirmation is False
    assert reply.text.startswith('Hay 7 tareas que coinciden con "taller":')
    assert [line for line in reply.text.splitlines() if line.startswith("- ")] == [
        f'- "Taller {n}" para el {(DUE + timedelta(days=n - 1)).strftime("%d/%m/%Y %H:%M")}'
        for n in range(1, 6)
    ]
    assert store.get(USER).pending is None
    assert {task.status for task in academic.list_tasks(USER, TaskFilters())} == {"pending"}


def test_complete_task_only_considers_pending_candidates_rf_agt_09():
    academic = InMemoryAcademicGateway()
    academic.add_task(USER, _task("Taller 1", DUE, status="completed"))
    academic.add_task(USER, _task("Taller 2", DUE + timedelta(days=1)))
    uc = _use_case([_complete("taller")], academic=academic)

    reply = uc.execute(_msg("ya entregue el taller"))

    assert reply.awaiting_confirmation is True
    assert '"Taller 2"' in reply.text


def test_complete_task_not_found_is_reported_rf_agt_09():
    uc = _use_case([_complete("ensayo")])

    reply = uc.execute(_msg("ya entregue el ensayo"))

    assert reply.text == replies.task_not_found("ensayo")


def test_complete_task_with_low_confidence_asks_to_rephrase_rf_agt_16():
    academic = InMemoryAcademicGateway()
    academic.add_task(USER, _task("Taller", DUE))
    uc = _use_case([_complete("taller", confidence=0.4)], academic=academic)

    reply = uc.execute(_msg("creo que el taller"))

    assert reply.text == replies.rephrase()
    assert reply.awaiting_confirmation is False


def _update(hint: str) -> Interpretation:
    return Interpretation(
        Intent.UPDATE_TASK, 0.9, task_hint=hint, task=ExtractedTaskData(due_at=DUE + timedelta(days=2))
    )


def test_update_task_not_found_is_reported_rf_agt_08():
    uc = _use_case([_update("ensayo")])

    reply = uc.execute(_msg("cambia el ensayo para el martes"))

    assert reply.text == replies.task_not_found("ensayo")
    assert reply.awaiting_confirmation is False


def test_update_task_with_several_matches_lists_five_and_changes_nothing_rf_agt_08():
    academic = InMemoryAcademicGateway()
    for day in range(6):
        academic.add_task(USER, _task(f"Quiz {day + 1}", DUE + timedelta(days=day)))
    store = InMemoryConversationStore()
    uc = _use_case([_update("quiz")], academic=academic, store=store)

    reply = uc.execute(_msg("mueve el quiz al martes"))

    assert reply.awaiting_confirmation is False
    assert sum(line.startswith("- ") for line in reply.text.splitlines()) == 5
    assert '"Quiz 6"' not in reply.text
    assert reply.text.endswith("Puedes ser mas especifico?")
    assert store.get(USER).pending is None


def test_update_task_with_one_match_waits_for_confirmation_rf_agt_08():
    academic = InMemoryAcademicGateway()
    academic.add_task(USER, _task("Ensayo final", DUE))
    uc = _use_case([_update("ensayo")], academic=academic)

    proposal = uc.execute(_msg("cambia el ensayo para el martes"))
    assert academic.list_tasks(USER, TaskFilters())[0].due_at == DUE
    uc.execute(_msg("si"))

    assert proposal.awaiting_confirmation is True
    assert academic.list_tasks(USER, TaskFilters())[0].due_at == DUE + timedelta(days=2)


def test_intent_outside_the_closed_list_gets_the_fixed_reply_rf_agt_02():
    llm = FakeLLM([Interpretation(Intent.UNKNOWN, 0.9)])
    uc = _use_case(None, llm=llm)

    reply = uc.execute(_msg("borra todas mis asignaturas"))

    assert reply.text == replies.not_understood()
    # Sin segunda llamada: ni interpretacion ni ayuda.
    assert llm.seen == ["borra todas mis asignaturas"]


# -- D4 · RF-AGT-11: consultar actividades ---------------------------------------


def test_query_lists_ten_by_due_date_with_priority_and_the_rest_rf_agt_11():
    academic = InMemoryAcademicGateway()
    priorities = ("high", "medium", "low")
    # Se agregan en desorden: la respuesta debe ordenarlas por fecha limite.
    for day in reversed(range(12)):
        academic.add_task(
            USER, _task(f"Actividad {day + 1:02d}", DUE + timedelta(days=day), priority=priorities[day % 3])
        )
    uc = _use_case([Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters())], academic=academic)

    reply = uc.execute(_msg("que tareas tengo?"))

    lines = reply.text.splitlines()
    assert lines[0] == "Tienes 12 actividad(es):"
    assert lines[1] == f'- "Actividad 01" para el {DUE.strftime("%d/%m/%Y %H:%M")}, prioridad alta'
    assert lines[2].endswith("prioridad media")
    assert lines[3].endswith("prioridad baja")
    assert [line.split('"')[1] for line in lines[1:11]] == [f"Actividad {n:02d}" for n in range(1, 11)]
    assert lines[11] == "...y 2 mas."
    assert len(lines) == 12


def test_query_filters_by_type_rf_agt_11():
    academic = InMemoryAcademicGateway()
    academic.add_task(USER, _task("Taller", DUE))
    academic.add_task(USER, _task("Parcial", DUE, type="exam"))
    uc = _use_case(
        [Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters(type="exam"))], academic=academic
    )

    reply = uc.execute(_msg("que examenes tengo?"))

    assert '"Parcial"' in reply.text
    assert '"Taller"' not in reply.text


def test_query_filters_by_status_and_period_rf_agt_11():
    academic = InMemoryAcademicGateway()
    academic.add_task(USER, _task("Vieja", DUE - timedelta(days=30), status="overdue"))
    academic.add_task(USER, _task("Hecha", DUE, status="completed"))
    academic.add_task(USER, _task("Abierta", DUE))
    filters = ExtractedFilters(status="completed", due_from=DUE - timedelta(days=1), due_to=DUE + timedelta(days=1))
    uc = _use_case([Interpretation(Intent.QUERY_TASKS, 0.9, filters=filters)], academic=academic)

    reply = uc.execute(_msg("que tareas complete esta semana?"))

    assert reply.text.splitlines()[1:] == [f'- "Hecha" para el {DUE.strftime("%d/%m/%Y %H:%M")}, completada']


def test_query_with_unknown_subject_asks_instead_of_listing_everything_rf_agt_10():
    academic = InMemoryAcademicGateway()
    academic.add_subject(USER, "Redes")
    academic.add_task(USER, _task("Taller", DUE))
    uc = _use_case(
        [Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters(subject="quimica"))], academic=academic
    )

    reply = uc.execute(_msg("que tengo en quimica?"))

    assert reply.text == replies.subject_not_found("quimica")


def test_query_shows_dates_in_colombia_time_rt_03():
    academic = InMemoryAcademicGateway()
    utc_due = datetime(2026, 9, 21, 4, 59, tzinfo=timezone.utc)
    academic.add_task(USER, _task("Taller", utc_due))
    uc = _use_case([Interpretation(Intent.QUERY_TASKS, 0.9, filters=ExtractedFilters())], academic=academic)

    reply = uc.execute(_msg("que tareas tengo?"))

    assert "para el 20/09/2026 23:59" in reply.text


# -- D5 · RF-AGT-12 y RF-AGT-13: resumen del periodo y horario ------------------


class SpyAcademic(InMemoryAcademicGateway):
    """Registra los limites con que el caso de uso pide el resumen y las clases."""

    def __init__(self) -> None:
        super().__init__()
        self.ranges: list[tuple[str, datetime, datetime]] = []

    def summarize_period(self, user_id, start, end):
        self.ranges.append(("summary", start, end))
        return super().summarize_period(user_id, start, end)

    def get_classes(self, user_id, start, end):
        self.ranges.append(("classes", start, end))
        return super().get_classes(user_id, start, end)


SEPTEMBER = ExtractedPeriod(start=date(2026, 9, 1), end=date(2026, 9, 30))
TOMORROW = ExtractedPeriod(start=date(2026, 9, 11), end=date(2026, 9, 11))


def test_period_bounds_are_whole_days_in_colombia_rt_03():
    start, end = SEPTEMBER.bounds()

    assert start == datetime(2026, 9, 1, 0, 0, tzinfo=COLOMBIA_TZ)
    assert end == datetime(2026, 10, 1, 0, 0, tzinfo=COLOMBIA_TZ)
    assert start.utcoffset() == timedelta(hours=-5)


def test_summary_uses_backend_counts_for_the_period_rf_agt_12():
    academic = SpyAcademic()
    academic.add_task(USER, _task("Taller", datetime(2026, 9, 15, 23, 59, tzinfo=COLOMBIA_TZ), subject="Redes"))
    academic.add_task(USER, _task("Quiz", datetime(2026, 9, 5, 10, 0, tzinfo=COLOMBIA_TZ), subject="Redes", status="completed"))
    academic.add_task(USER, _task("Ensayo", datetime(2026, 9, 2, 8, 0, tzinfo=COLOMBIA_TZ), subject="Ética", status="overdue"))
    academic.add_task(USER, _task("Fuera", datetime(2026, 10, 1, 0, 0, tzinfo=COLOMBIA_TZ), subject="Redes"))
    llm = FakeLLM([Interpretation(Intent.SUMMARY, 0.9, period=SEPTEMBER)])
    uc = _use_case(None, academic=academic, llm=llm)

    reply = uc.execute(_msg("dame el resumen de tareas de este mes"))

    assert reply.text.splitlines() == [
        "Resumen del 01/09/2026 al 30/09/2026: 1 pendiente(s), 1 completada(s) y 1 vencida(s).",
        "- Redes: 1 pendiente(s), 1 completada(s), 0 vencida(s)",
        "- Ética: 0 pendiente(s), 0 completada(s), 1 vencida(s)",
        'Proxima por vencer: "Taller" (Redes) el 15/09/2026 23:59.',
    ]
    assert academic.ranges == [("summary", *SEPTEMBER.bounds())]
    assert len(llm.seen) == 1


def test_summary_without_period_asks_for_it_rf_agt_12():
    academic = SpyAcademic()
    uc = _use_case([Interpretation(Intent.SUMMARY, 0.9)], academic=academic)

    reply = uc.execute(_msg("dame el resumen"))

    assert reply.text == replies.missing_summary_period()
    assert academic.ranges == []


def _class(subject: str, start: datetime, room: str | None = None, subject_id: str | None = None) -> ClassView:
    return ClassView(
        subject_id=subject_id or subject,
        subject_name=subject,
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        room=room,
    )


def test_schedule_lists_classes_of_the_period_in_colombia_time_rf_agt_13():
    academic = SpyAcademic()
    academic.add_class(USER, _class("Física", datetime(2026, 9, 11, 14, 0, tzinfo=COLOMBIA_TZ), room="201"))
    academic.add_class(USER, _class("Redes", datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)))
    academic.add_class(USER, _class("Ética", datetime(2026, 9, 12, 8, 0, tzinfo=COLOMBIA_TZ)))
    uc = _use_case([Interpretation(Intent.QUERY_SCHEDULE, 0.9, period=TOMORROW)], academic=academic)

    reply = uc.execute(_msg("que clases tengo manana?"))

    assert reply.text.splitlines() == [
        "Tienes 2 clase(s):",
        "- viernes 11/09/2026 07:00-09:00 Redes",
        "- viernes 11/09/2026 14:00-16:00 Física, salon 201",
    ]
    assert academic.ranges == [("classes", *TOMORROW.bounds())]


def test_schedule_filters_by_the_resolved_subject_rf_agt_13():
    academic = SpyAcademic()
    physics = academic.add_subject(USER, "Física")
    academic.add_subject(USER, "Redes")
    thursday = datetime(2026, 9, 17, 10, 0, tzinfo=COLOMBIA_TZ)
    academic.add_class(USER, _class("Física", thursday, subject_id=physics.id))
    academic.add_class(USER, _class("Redes", thursday + timedelta(hours=3), subject_id="otra"))
    period = ExtractedPeriod(start=date(2026, 9, 17), end=date(2026, 9, 17))
    uc = _use_case(
        [Interpretation(Intent.QUERY_SCHEDULE, 0.9, period=period, filters=ExtractedFilters(subject="fisica"))],
        academic=academic,
    )

    reply = uc.execute(_msg("a que hora tengo fisica el jueves?"))

    assert reply.text.splitlines() == ["Tienes 1 clase(s):", "- jueves 17/09/2026 10:00-12:00 Física"]


def test_schedule_lists_at_most_ten_classes_and_the_rest_rf_agt_13():
    academic = SpyAcademic()
    monday = datetime(2026, 9, 14, 6, 0, tzinfo=COLOMBIA_TZ)
    for hour in range(12):
        academic.add_class(USER, _class(f"Clase {hour + 1:02d}", monday + timedelta(hours=hour)))
    week = ExtractedPeriod(start=date(2026, 9, 14), end=date(2026, 9, 20))
    uc = _use_case([Interpretation(Intent.QUERY_SCHEDULE, 0.9, period=week)], academic=academic)

    reply = uc.execute(_msg("que clases tengo la proxima semana?"))

    lines = reply.text.splitlines()
    assert lines[0] == "Tienes 12 clase(s):"
    assert [line.rsplit(" ", 2)[-2:] for line in lines[1:11]] == [["Clase", f"{n:02d}"] for n in range(1, 11)]
    assert lines[11] == "...y 2 mas."
    assert len(lines) == 12


def test_schedule_without_period_asks_for_it_rf_agt_13():
    academic = SpyAcademic()
    uc = _use_case([Interpretation(Intent.QUERY_SCHEDULE, 0.9)], academic=academic)

    reply = uc.execute(_msg("mis clases"))

    assert reply.text == replies.missing_schedule_period()
    assert academic.ranges == []


def test_schedule_without_classes_says_so_rf_agt_13():
    uc = _use_case([Interpretation(Intent.QUERY_SCHEDULE, 0.9, period=TOMORROW)])

    reply = uc.execute(_msg("que clases tengo manana?"))

    assert reply.text == "No tienes clases registradas en ese periodo."


# -- D6 · RF-AGT-14: ayuda cortada por el limite de tokens ----------------------


class TruncatingLLM(FakeLLM):
    """La ayuda llega cortada por el limite de tokens de salida."""

    def __init__(self, finish_reason: str) -> None:
        super().__init__([Interpretation(Intent.SYSTEM_HELP, 0.9)], help_answer="TAIA te permite crear tar")
        self._finish = finish_reason

    def last_usage(self) -> LLMUsage | None:
        return LLMUsage(model="test", finish_reason=self._finish)


def test_help_cut_by_max_tokens_is_replaced_by_a_fixed_message_rf_agt_14():
    uc = _use_case(None, llm=TruncatingLLM("MAX_TOKENS"))

    reply = uc.execute(_msg("como funciona TAIA?"))

    assert reply.text == replies.help_truncated()
    assert "crear tar" not in reply.text


def test_complete_help_answer_is_shown_rf_agt_14():
    uc = _use_case(None, llm=TruncatingLLM("STOP"))

    reply = uc.execute(_msg("como funciona TAIA?"))

    assert reply.text == "TAIA te permite crear tar"
