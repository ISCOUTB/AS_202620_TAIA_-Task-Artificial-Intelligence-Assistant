"""Adaptador de IA hacia Academic (RF-AGT-05, 09, 10, 12 y 13).

`AcademicTaskManagement` es el real, sobre los repositorios de Academic.
`AcademicInsights` lo implementa el frente C: aquí se usa un doble del puerto.
"""

from datetime import datetime, timedelta, timezone
import uuid

import pytest

from app.modules.academic.adapters.outbound.repository_provider import get_subject_repository
from app.modules.academic.application.ports.inbound.academic_insights import (
    AcademicPeriodSummary,
    ClassOccurrence,
    SubjectTaskCounts,
)
from app.modules.academic.application.ports.inbound.task_management import AcademicSubjectRef
from app.modules.academic.domain.entities.subject import Subject
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.application.dto import NewTask, TaskFilters
from app.modules.ai.application.ports.academic_gateway import AcademicError, TaskDataRejected
from app.shared.clock import now_bogota

DUE = now_bogota() + timedelta(days=3)
TZ = timezone(timedelta(hours=-5))


class FakeInsights:
    """Doble de AcademicInsights que registra con qué usuario se le llamó."""

    def __init__(self, subjects=(), summary=None, classes=()):
        self._subjects = list(subjects)
        self._summary = summary
        self._classes = list(classes)
        self.calls: list[tuple[str, uuid.UUID]] = []

    def match_subjects(self, user_id, text, limit=5):
        self.calls.append(("match_subjects", user_id))
        return self._subjects[:limit]

    def summarize_period(self, user_id, start, end):
        self.calls.append(("summarize_period", user_id))
        return self._summary

    def get_classes(self, user_id, start, end):
        self.calls.append(("get_classes", user_id))
        return self._classes


def _user_with_subject(name: str = "Arquitectura de Software") -> tuple[uuid.UUID, Subject]:
    user_id = uuid.uuid4()
    subject = Subject.create(user_id, name)
    get_subject_repository().add(subject)
    return user_id, subject


def test_ai_gateway_creates_with_the_resolved_subject_id_and_type_rf_agt_05():
    user_id, subject = _user_with_subject()
    gateway = AcademicGatewayAdapter()

    created = gateway.create_task(
        str(user_id),
        NewTask(title="Parcial 1", due_at=DUE, subject_id=str(subject.id), type="exam"),
    )

    found = gateway.list_tasks(str(user_id), TaskFilters())
    assert found == [created]
    assert found[0].subject == "Arquitectura de Software"
    assert found[0].type == "exam"
    assert found[0].priority == "medium"


def test_ai_gateway_filters_by_subject_id_and_type():
    user_id, subject = _user_with_subject()
    _, other_subject = _user_with_subject("Física")
    gateway = AcademicGatewayAdapter()
    gateway.create_task(str(user_id), NewTask(title="Taller", due_at=DUE, subject_id=str(subject.id)))
    gateway.create_task(str(user_id), NewTask(title="Parcial", due_at=DUE, subject_id=str(subject.id), type="exam"))

    by_type = gateway.list_tasks(str(user_id), TaskFilters(subject_id=str(subject.id), type="exam"))

    assert [task.title for task in by_type] == ["Parcial"]
    assert gateway.list_tasks(str(user_id), TaskFilters(subject_id=str(other_subject.id))) == []



def test_ai_gateway_sends_the_type_filter_to_academic_rf_agt_11():
    """El tipo se filtra en la consulta de Academic, no sobre la página ya leída (P-D-01)."""

    class _AcademicSpy:
        def __init__(self) -> None:
            self.queries = []

        def list_tasks(self, user_id, query):
            self.queries.append(query)
            return type("Page", (), {"items": []})()

    academic = _AcademicSpy()

    AcademicGatewayAdapter(academic=academic).list_tasks(str(uuid.uuid4()), TaskFilters(type="exam"))

    assert [query.type for query in academic.queries] == ["exam"]

def test_ai_gateway_rejects_missing_or_foreign_subject():
    user_id, _ = _user_with_subject()
    _, foreign = _user_with_subject("Química")
    gateway = AcademicGatewayAdapter()
    owner = str(user_id)
    missing = NewTask(title="Tarea", due_at=DUE)
    foreign_task = NewTask(title="Tarea", due_at=DUE, subject_id=str(foreign.id))

    with pytest.raises(TaskDataRejected, match="Indica la asignatura"):
        gateway.create_task(owner, missing)
    with pytest.raises(TaskDataRejected):
        gateway.create_task(owner, foreign_task)


def test_ai_gateway_completes_only_own_tasks_rf_agt_09():
    owner, subject = _user_with_subject()
    gateway = AcademicGatewayAdapter()
    created = gateway.create_task(str(owner), NewTask(title="Taller", due_at=DUE, subject_id=str(subject.id)))
    stranger = str(uuid.uuid4())

    with pytest.raises(TaskDataRejected):
        gateway.complete_task(stranger, created.id)
    assert gateway.complete_task(str(owner), created.id).status == "completed"


def test_ai_gateway_keeps_users_isolated():
    owner, subject = _user_with_subject()
    other = uuid.uuid4()
    gateway = AcademicGatewayAdapter()

    gateway.create_task(str(owner), NewTask(title="Solo del dueño", due_at=DUE, subject_id=str(subject.id)))

    assert gateway.list_tasks(str(other), TaskFilters()) == []


def test_ai_gateway_matches_subjects_with_academic_insights_rf_agt_10():
    user_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    insights = FakeInsights([AcademicSubjectRef(subject_id=subject_id, name="Matemáticas Básicas")])
    gateway = AcademicGatewayAdapter(insights=insights)

    options = gateway.match_subjects(str(user_id), "mate basicas")

    assert [(o.id, o.name) for o in options] == [(str(subject_id), "Matemáticas Básicas")]
    assert insights.calls == [("match_subjects", user_id)]


def test_ai_gateway_maps_summary_and_classes_rf_agt_12_rf_agt_13():
    user_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    start = datetime(2026, 9, 1, tzinfo=TZ)
    end = datetime(2026, 10, 1, tzinfo=TZ)
    insights = FakeInsights(
        summary=AcademicPeriodSummary(
            start=start, end=end, pending=2, completed=1, overdue=0,
            by_subject=[SubjectTaskCounts(subject_id, "Física", 2, 1, 0)], next_due=None,
        ),
        classes=[ClassOccurrence(subject_id, "Física", start, start + timedelta(hours=2), "201")],
    )
    gateway = AcademicGatewayAdapter(insights=insights)

    summary = gateway.summarize_period(str(user_id), start, end)
    classes = gateway.get_classes(str(user_id), start, end)

    assert (summary.pending, summary.completed, summary.by_subject[0].name) == (2, 1, "Física")
    assert classes[0].subject_id == str(subject_id)
    assert classes[0].room == "201"
    assert insights.calls == [("summarize_period", user_id), ("get_classes", user_id)]


def test_ai_gateway_without_academic_insights_is_an_academic_error(monkeypatch):
    """Sin AcademicInsights configurado, el caso de uso responde servicio no disponible."""
    from app.modules.academic.application.ports.inbound import academic_insights

    monkeypatch.setattr(academic_insights, "_service", None)
    gateway = AcademicGatewayAdapter()

    with pytest.raises(AcademicError):
        gateway.match_subjects(str(uuid.uuid4()), "física")
