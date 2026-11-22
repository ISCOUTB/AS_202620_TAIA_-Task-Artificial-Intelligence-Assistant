"""Detalle de una actividad con sus recordatorios (RF-TAR-05).

Los recordatorios vienen del puerto `TaskReminderReader` de Reminders, aquí con un doble.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.reminders.application.ports.inbound import task_reminder_sync as reminder_port
from app.modules.reminders.application.ports.inbound.task_reminder_sync import TaskReminderView
from app.shared.clock import now_bogota
from tests.helpers import create_subject, future_iso, register_and_login

client = TestClient(app)


class FakeReminderReader:
    """Doble de `TaskReminderReader`: devuelve recordatorios fijos y registra quién pregunta."""

    def __init__(self) -> None:
        self.asked: list[tuple[uuid.UUID, uuid.UUID]] = []

    def list_for_task(self, user_id, task_id) -> list[TaskReminderView]:
        self.asked.append((user_id, task_id))
        first = now_bogota().replace(microsecond=0) + timedelta(days=1)
        return [
            TaskReminderView(uuid.uuid4(), first, "Recuerda: Informe", "automatic", "pending"),
            TaskReminderView(uuid.uuid4(), first + timedelta(days=2), "Lleva el informe", "custom", "pending"),
        ]


@pytest.fixture
def reader(monkeypatch) -> FakeReminderReader:
    double = FakeReminderReader()
    monkeypatch.setattr(reminder_port, "_reader", double)
    return double


def _task(headers, **extra) -> dict:
    payload = {
        "subject_id": create_subject(client, headers, f"Física {uuid.uuid4().hex[:6]}"),
        "title": "Informe",
        "description": "Laboratorio 2",
        "due_at": future_iso(days=1),
        "type": "exam",
        **extra,
    }
    response = client.post("/academic/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_detail_includes_fields_priority_dates_and_reminders_rf_tar_05(reader):
    headers = register_and_login(client)
    task = _task(headers)

    response = client.get(f"/academic/tasks/{task['id']}", headers=headers)

    body = response.json()
    assert response.status_code == 200
    assert {key: body[key] for key in ("title", "description", "type", "subject_name")} == {
        "title": "Informe", "description": "Laboratorio 2", "type": "exam", "subject_name": task["subject_name"],
    }
    assert body["priority"] == "high"
    assert body["created_at"] is not None
    assert body["completed_at"] is None
    assert [reminder["origin"] for reminder in body["reminders"]] == ["automatic", "custom"]
    assert set(body["reminders"][0]) == {"id", "scheduled_at", "message", "origin", "status"}
    assert reader.asked[0][1] == uuid.UUID(task["id"])


def test_detail_of_completed_task_shows_completed_at_rf_tar_05(reader):
    headers = register_and_login(client)
    task = _task(headers)
    client.patch(f"/academic/tasks/{task['id']}/complete", headers=headers)

    body = client.get(f"/academic/tasks/{task['id']}", headers=headers).json()

    assert body["status"] == "completed"
    assert body["priority"] is None
    assert datetime.fromisoformat(body["completed_at"]).utcoffset() == timedelta(hours=-5)


def test_detail_of_other_users_task_is_404_and_reads_no_reminders_rt_02(reader):
    task = _task(register_and_login(client))

    response = client.get(f"/academic/tasks/{task['id']}", headers=register_and_login(client))

    assert response.status_code == 404
    assert reader.asked == []


def test_detail_fails_when_reminder_reader_is_not_configured_h_12(monkeypatch):
    """Sin el puerto de Reminders, el detalle falla con error en vez de omitir los recordatorios (H-12, P-C-02)."""

    headers = register_and_login(client)
    task = _task(headers)
    monkeypatch.setattr(reminder_port, "_reader", None)

    with pytest.raises(RuntimeError):
        client.get(f"/academic/tasks/{task['id']}", headers=headers)
