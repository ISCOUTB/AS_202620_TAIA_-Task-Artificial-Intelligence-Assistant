from datetime import timedelta
import uuid

import pytest

from app.modules.academic.adapters.outbound.repository_provider import get_subject_repository
from app.modules.academic.domain.entities.subject import Subject
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.application.dto import NewTask, TaskFilters
from app.modules.ai.application.ports.academic_gateway import TaskDataRejected
from app.shared.clock import now_bogota

DUE = now_bogota() + timedelta(days=3)


def _user_with_subject(name: str = "Arquitectura de Software", alias: str | None = None) -> uuid.UUID:
    user_id = uuid.uuid4()
    subject = Subject.create(user_id, name)
    if alias:
        subject.add_alias(alias)
    get_subject_repository().add(subject)
    return user_id


def test_ai_gateway_creates_and_reads_from_academic_repository():
    user_id = _user_with_subject()
    gateway = AcademicGatewayAdapter()

    created = gateway.create_task(
        str(user_id),
        NewTask(title="Preparar parcial", due_at=DUE, subject="arquitectura de software"),
    )

    found = gateway.list_tasks(str(user_id), TaskFilters())

    assert found == [created]
    assert found[0].subject == "Arquitectura de Software"
    assert found[0].status == "pending"


def test_ai_gateway_resolves_subject_by_alias_and_filters_by_it():
    user_id = _user_with_subject("Matemáticas Básicas", alias="Mate básicas")
    gateway = AcademicGatewayAdapter()
    gateway.create_task(str(user_id), NewTask(title="Taller 3", due_at=DUE, subject="mate basicas"))

    assert [t.title for t in gateway.list_tasks(str(user_id), TaskFilters(subject="Matematicas basicas"))] == ["Taller 3"]
    assert gateway.list_tasks(str(user_id), TaskFilters(subject="Física")) == []


def test_ai_gateway_rejects_unknown_or_missing_subject():
    user_id = _user_with_subject()
    gateway = AcademicGatewayAdapter()

    with pytest.raises(TaskDataRejected, match="No encontré la asignatura"):
        gateway.create_task(str(user_id), NewTask(title="Tarea", due_at=DUE, subject="Química"))
    with pytest.raises(TaskDataRejected, match="Indica la asignatura"):
        gateway.create_task(str(user_id), NewTask(title="Tarea", due_at=DUE))


def test_ai_gateway_keeps_users_isolated():
    owner = _user_with_subject()
    other = uuid.uuid4()
    gateway = AcademicGatewayAdapter()

    gateway.create_task(str(owner), NewTask(title="Solo del dueño", due_at=DUE, subject="Arquitectura de Software"))

    assert gateway.list_tasks(str(other), TaskFilters()) == []
