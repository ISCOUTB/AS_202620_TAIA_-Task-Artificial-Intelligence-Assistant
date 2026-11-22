"""Academic avisa a Reminders del ciclo de vida de cada actividad (RF-TAR-02, 06, 07, 08, 10; RF-REC-06).

Reminders lo implementa otro frente: aquí se usa un doble del puerto `TaskReminderSync`
que registra las llamadas y emula cuántos recordatorios genera cada opción.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.academic.adapters.outbound.in_memory_structure_repositories import InMemorySubjectRepository
from app.modules.academic.adapters.outbound.in_memory_task_repository import InMemoryTaskRepository
from app.modules.academic.application.errors import InvalidReminderPlanError
from app.modules.academic.application.services.task_management import AcademicTaskManagementService
from app.modules.academic.domain.entities.subject import Subject
from app.modules.reminders.application.ports.inbound import task_reminder_sync as reminder_port
from app.modules.reminders.application.ports.inbound.task_reminder_sync import ReminderPlan
from app.shared.clock import BOGOTA_TZ, now_bogota
from tests.helpers import create_subject, future_iso, register_and_login

client = TestClient(app)


class RecordingReminderSync:
    """Doble de `TaskReminderSync`: guarda cada llamada y los recordatorios que generaría."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.generated: dict[uuid.UUID, int] = {}

    def on_task_created(self, user_id, task_id, due_at, plan: ReminderPlan) -> None:
        self.calls.append(("created", user_id, task_id, due_at, plan))
        self.generated[task_id] = {"none": 0, "default": 2, "custom": len(plan.custom_at)}[plan.mode]

    def on_due_changed(self, user_id, task_id, due_at) -> None:
        self.calls.append(("due_changed", user_id, task_id, due_at))

    def on_task_closed(self, user_id, task_id) -> None:
        self.calls.append(("closed", user_id, task_id))
        self.generated[task_id] = 0

    def on_task_reopened(self, user_id, task_id, due_at) -> None:
        self.calls.append(("reopened", user_id, task_id, due_at))

    def cancel_all_for_user(self, user_id) -> None:
        self.calls.append(("cancel_all", user_id))

    def kinds(self, task_id) -> list[str]:
        return [call[0] for call in self.calls if call[2] == task_id]


@pytest.fixture
def reminders(monkeypatch) -> RecordingReminderSync:
    double = RecordingReminderSync()
    monkeypatch.setattr(reminder_port, "_service", double)
    return double


def _create(headers, subject_id=None, **extra):
    payload = {
        "subject_id": subject_id or create_subject(client, headers, f"Física {uuid.uuid4().hex[:6]}"),
        "title": "Informe",
        "due_at": future_iso(days=8),
        **extra,
    }
    return client.post("/academic/tasks", json=payload, headers=headers)


# RF-TAR-02 · opción de recordatorios al crear


def test_create_without_option_applies_default_policy_in_same_operation_rf_tar_02(reminders):
    headers = register_and_login(client)

    task = _create(headers).json()

    [call] = reminders.calls
    assert call[0] == "created"
    assert call[2] == uuid.UUID(task["id"])
    assert call[4] == ReminderPlan(mode="default")
    assert reminders.generated[uuid.UUID(task["id"])] > 0


def test_create_with_default_policy_generates_reminders_rf_tar_02(reminders):
    headers = register_and_login(client)

    task = _create(headers, reminders={"mode": "default"}).json()

    assert reminders.calls[0][4].mode == "default"
    assert reminders.generated[uuid.UUID(task["id"])] > 0


def test_create_without_reminders_generates_none_rf_tar_02(reminders):
    headers = register_and_login(client)

    task = _create(headers, reminders={"mode": "none"}).json()

    assert reminders.calls[0][4] == ReminderPlan(mode="none")
    assert reminders.generated[uuid.UUID(task["id"])] == 0


def test_create_with_custom_reminders_sends_bogota_dates_rf_tar_02(reminders):
    headers = register_and_login(client)
    day = (now_bogota() + timedelta(days=3)).date().isoformat()
    later = (now_bogota() + timedelta(days=5)).isoformat()

    response = _create(headers, reminders={"mode": "custom", "custom_at": [later, f"{day}T18:00:00"]})

    assert response.status_code == 201
    plan = reminders.calls[0][4]
    assert plan.mode == "custom"
    assert plan.custom_at[0] == datetime.fromisoformat(f"{day}T18:00:00").replace(tzinfo=BOGOTA_TZ)
    assert len(plan.custom_at) == 2
    assert all(moment.utcoffset() == timedelta(hours=-5) for moment in plan.custom_at)


@pytest.mark.parametrize(
    "option",
    [
        {"mode": "custom", "custom_at": []},
        {"mode": "custom", "custom_at": [(now_bogota() - timedelta(hours=1)).isoformat()]},
        {"mode": "custom", "custom_at": [future_iso(days=9)]},
        {"mode": "default", "custom_at": [future_iso(days=2)]},
        {"mode": "weekly"},
    ],
)
def test_invalid_reminder_option_returns_422_and_creates_nothing_rf_tar_02(reminders, option):
    headers = register_and_login(client)

    response = _create(headers, reminders=option)

    assert response.status_code == 422
    assert reminders.calls == []
    assert client.get("/academic/tasks", headers=headers).json()["total"] == 0


def _custom_dates(count: int) -> list[str]:
    start = now_bogota() + timedelta(days=1)
    return [(start + timedelta(hours=hour)).isoformat() for hour in range(count)]


def test_create_with_eleven_custom_dates_returns_422_and_creates_nothing_rf_tar_02(reminders):
    headers = register_and_login(client)

    response = _create(headers, reminders={"mode": "custom", "custom_at": _custom_dates(11)})

    assert response.status_code == 422
    assert "10" in response.json()["detail"]
    assert reminders.calls == []
    assert client.get("/academic/tasks", headers=headers).json()["total"] == 0


def test_create_with_ten_custom_dates_is_accepted_rf_tar_02(reminders):
    headers = register_and_login(client)

    response = _create(headers, reminders={"mode": "custom", "custom_at": _custom_dates(10)})

    assert response.status_code == 201
    assert len(reminders.calls[0][4].custom_at) == 10


def test_agent_port_applies_default_policy_rf_agt_07():
    """`AcademicTaskManagement.create_task`, que usa el agente, no recibe opción: aplica la política por defecto."""

    subjects = InMemorySubjectRepository()
    owner = uuid.uuid4()
    subject = Subject.create(owner, "Física")
    subjects.add(subject)
    double = RecordingReminderSync()
    service = AcademicTaskManagementService(InMemoryTaskRepository(subjects), subjects, reminders=double)

    task = service.create_task(owner, subject.id, "Laboratorio", now_bogota() + timedelta(days=4))

    assert double.calls == [("created", owner, task.task_id, task.due_at, ReminderPlan(mode="default"))]


def test_service_rejects_inconsistent_plan_before_saving_rf_tar_02():
    subjects = InMemorySubjectRepository()
    owner = uuid.uuid4()
    subject = Subject.create(owner, "Física")
    subjects.add(subject)
    tasks = InMemoryTaskRepository(subjects)
    double = RecordingReminderSync()
    service = AcademicTaskManagementService(tasks, subjects, reminders=double)
    due = now_bogota() + timedelta(days=4)
    plan = ReminderPlan(mode="custom", custom_at=(due + timedelta(hours=1),))

    with pytest.raises(InvalidReminderPlanError):
        service.create_task(owner, subject.id, "Laboratorio", due, reminders=plan)

    assert double.calls == []
    assert tasks.count_open_by_subject(owner) == {}


# RF-TAR-06 · cambio de fecha límite


def test_changing_due_at_of_pending_task_recalculates_reminders_rf_tar_06(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]
    new_due = future_iso(days=15)

    body = client.patch(f"/academic/tasks/{task_id}", json={"due_at": new_due}, headers=headers).json()

    kind, _, called_task, due_at = reminders.calls[-1]
    assert (kind, called_task) == ("due_changed", uuid.UUID(task_id))
    assert due_at == datetime.fromisoformat(body["due_at"])


def test_update_without_due_change_does_not_touch_reminders_rf_tar_06(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]

    client.patch(f"/academic/tasks/{task_id}", json={"title": "Informe final"}, headers=headers)

    assert reminders.kinds(uuid.UUID(task_id)) == ["created"]


def test_due_change_of_completed_task_does_not_recalculate_rf_tar_06(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]
    client.patch(f"/academic/tasks/{task_id}/complete", headers=headers)

    client.patch(f"/academic/tasks/{task_id}", json={"due_at": future_iso(days=20)}, headers=headers)

    assert reminders.kinds(uuid.UUID(task_id)) == ["created", "closed"]


def test_change_to_other_users_subject_returns_404_without_sync_rf_tar_06(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]
    foreign = create_subject(client, register_and_login(client))

    response = client.patch(
        f"/academic/tasks/{task_id}", json={"subject_id": foreign, "due_at": future_iso(days=20)}, headers=headers
    )

    assert response.status_code == 404
    assert reminders.kinds(uuid.UUID(task_id)) == ["created"]


# RF-TAR-07 · completar


def test_complete_cancels_pending_reminders_and_is_idempotent_rf_tar_07(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]

    first = client.patch(f"/academic/tasks/{task_id}/complete", headers=headers).json()
    second = client.patch(f"/academic/tasks/{task_id}/complete", headers=headers).json()

    assert reminders.kinds(uuid.UUID(task_id))[:2] == ["created", "closed"]
    assert reminders.generated[uuid.UUID(task_id)] == 0
    assert second["completed_at"] == first["completed_at"]
    assert datetime.fromisoformat(first["completed_at"]).utcoffset() == timedelta(hours=-5)


# RF-TAR-08 · reabrir


def test_reopen_with_future_due_regenerates_reminders_rf_tar_08(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]
    client.patch(f"/academic/tasks/{task_id}/complete", headers=headers)

    body = client.patch(f"/academic/tasks/{task_id}/reopen", headers=headers).json()

    assert body["completed_at"] is None
    assert reminders.kinds(uuid.UUID(task_id)) == ["created", "closed", "reopened"]


def test_reopen_after_due_date_does_not_regenerate_rf_tar_08():
    subjects = InMemorySubjectRepository()
    owner = uuid.uuid4()
    subject = Subject.create(owner, "Física")
    subjects.add(subject)
    clock = {"now": now_bogota()}
    double = RecordingReminderSync()
    service = AcademicTaskManagementService(
        InMemoryTaskRepository(subjects), subjects, clock=lambda: clock["now"], reminders=double
    )
    task = service.create_task(owner, subject.id, "Laboratorio", clock["now"] + timedelta(days=1))
    service.complete_task(task.task_id, owner)
    clock["now"] += timedelta(days=2)

    reopened = service.reopen_task(task.task_id, owner)

    assert reopened.completed_at is None
    assert reopened.status == "overdue"
    assert [call[0] for call in double.calls] == ["created", "closed"]


def test_reopen_of_task_not_completed_does_not_regenerate_rf_tar_08(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]

    client.patch(f"/academic/tasks/{task_id}/reopen", headers=headers)

    assert reminders.kinds(uuid.UUID(task_id)) == ["created"]


# RF-TAR-10 · eliminar


def test_delete_cancels_reminders_and_hides_task_rf_tar_10(reminders):
    headers = register_and_login(client)
    task_id = _create(headers).json()["id"]

    response = client.delete(f"/academic/tasks/{task_id}", headers=headers)

    assert response.status_code == 204
    assert reminders.kinds(uuid.UUID(task_id)) == ["created", "closed"]
    assert reminders.generated[uuid.UUID(task_id)] == 0
    assert client.get(f"/academic/tasks/{task_id}", headers=headers).status_code == 404


def test_delete_other_users_task_returns_404_without_sync_rf_tar_10(reminders):
    task_id = _create(register_and_login(client)).json()["id"]

    response = client.delete(f"/academic/tasks/{task_id}", headers=register_and_login(client))

    assert response.status_code == 404
    assert reminders.kinds(uuid.UUID(task_id)) == ["created"]


def test_creating_a_task_fails_when_reminders_port_is_not_configured_h_12(monkeypatch):
    """Sin el puerto de Reminders, crear una actividad falla con error (H-12, P-C-02)."""

    headers = register_and_login(client)
    subject_id = create_subject(client, headers, f"Física {uuid.uuid4().hex[:6]}")
    monkeypatch.setattr(reminder_port, "_service", None)

    with pytest.raises(RuntimeError):
        _create(headers, subject_id)
