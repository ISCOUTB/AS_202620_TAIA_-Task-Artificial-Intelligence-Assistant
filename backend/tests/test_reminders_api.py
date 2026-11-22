"""API de recordatorios: RF-REC-01, 03, 04 y 05, RT-01, RT-02 y RT-05."""

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.modules.reminders.domain.entities import Notification
from app.shared.clock import now_bogota
from tests import helpers

client = TestClient(app)


def future_iso(hours: float = 2) -> str:
    return (now_bogota() + timedelta(hours=hours)).isoformat()


def _owner_with_task(title: str = "Informe") -> tuple[dict[str, str], str]:
    headers = helpers.register_and_login(client)
    return headers, helpers.create_task(client, headers, title)


def _create(headers, task_id, **extra):
    return client.post("/reminders", headers=headers,
                       json={"task_id": task_id, "scheduled_at": future_iso(), **extra})


def test_reminders_require_authentication_rt_01():
    assert client.get("/reminders").status_code == 401
    assert client.post("/reminders", json={}).status_code == 401


def test_create_list_edit_and_delete_rf_rec_01_03_04_05():
    headers, task_id = _owner_with_task()

    created = _create(headers, task_id, custom_message="Revisar entrega")
    assert created.status_code == 201, created.text
    body = created.json()
    assert set(body) == {"id", "task_id", "scheduled_at", "custom_message", "origin", "status"}
    assert (body["task_id"], body["custom_message"], body["origin"], body["status"]) == (
        task_id, "Revisar entrega", "custom", "pending")
    reminder_id = body["id"]

    # La tarea ya trae los recordatorios automáticos de la política por defecto (RF-REC-02).
    listed = client.get("/reminders", headers=headers).json()
    assert [item["id"] for item in listed if item["origin"] == "custom"] == [reminder_id]
    assert {item["origin"] for item in listed} == {"automatic", "custom"}

    edited = client.patch(f"/reminders/{reminder_id}", headers=headers,
                          json={"custom_message": "Revisar entrega final", "scheduled_at": future_iso(3)})
    assert edited.status_code == 200, edited.text
    assert edited.json()["custom_message"] == "Revisar entrega final"

    assert client.delete(f"/reminders/{reminder_id}", headers=headers).status_code == 204
    assert client.get(f"/reminders/{reminder_id}", headers=headers).status_code == 404


def test_message_is_optional_rf_rec_01():
    headers, task_id = _owner_with_task()

    created = _create(headers, task_id)

    assert created.status_code == 201
    assert created.json()["custom_message"] is None


def test_naive_date_is_colombian_time_rf_rec_01_rt_03():
    headers, task_id = _owner_with_task()
    naive = (now_bogota() + timedelta(hours=2)).replace(tzinfo=None, microsecond=0)

    created = client.post("/reminders", headers=headers, json={"task_id": task_id, "scheduled_at": naive.isoformat()})

    assert created.status_code == 201
    assert created.json()["scheduled_at"] == naive.isoformat() + "-05:00"


def test_past_date_is_rejected_rf_rec_01_rt_05():
    headers, task_id = _owner_with_task()

    response = _create(headers, task_id, scheduled_at=future_iso(-1))

    assert response.status_code == 422
    assert "futura" in response.json()["detail"]


def test_date_after_due_is_rejected_rf_rec_01_rt_05():
    headers, task_id = _owner_with_task()

    response = _create(headers, task_id, scheduled_at=future_iso(24 * 30))

    assert response.status_code == 422


def test_completed_task_does_not_accept_reminders_rf_rec_01_rt_05():
    headers, task_id = _owner_with_task()
    assert client.patch(f"/academic/tasks/{task_id}/complete", headers=headers).status_code == 200

    response = _create(headers, task_id)

    assert response.status_code == 409


def test_another_users_task_is_not_found_rf_rec_01_rt_02():
    _, task_id = _owner_with_task("Tarea privada")
    other = helpers.register_and_login(client)

    response = _create(other, task_id)

    assert response.status_code == 404


def test_another_users_reminder_is_not_found_rt_02():
    owner, task_id = _owner_with_task()
    reminder_id = _create(owner, task_id).json()["id"]
    other = helpers.register_and_login(client)

    assert client.get(f"/reminders/{reminder_id}", headers=other).status_code == 404
    assert client.patch(f"/reminders/{reminder_id}", headers=other, json={"custom_message": "x"}).status_code == 404
    assert client.delete(f"/reminders/{reminder_id}", headers=other).status_code == 404
    assert client.get("/reminders", headers=other).json() == []


def _mark_sent(reminder_id: str) -> None:
    reminder_uuid = uuid.UUID(reminder_id)
    claimed = main.reminder_repository.claim(
        reminder_uuid,
        Notification(id=uuid.uuid4(), reminder_id=reminder_uuid, message="Recuerda", created_at=now_bogota()),
    )
    assert claimed


def test_sent_reminder_cannot_be_edited_rf_rec_04():
    headers, task_id = _owner_with_task()
    reminder_id = _create(headers, task_id).json()["id"]
    _mark_sent(reminder_id)

    response = client.patch(f"/reminders/{reminder_id}", headers=headers, json={"custom_message": "Cambio"})

    assert response.status_code == 409


def test_sent_reminder_cannot_be_deleted_rf_rec_05():
    headers, task_id = _owner_with_task()
    reminder_id = _create(headers, task_id).json()["id"]
    _mark_sent(reminder_id)

    response = client.delete(f"/reminders/{reminder_id}", headers=headers)

    assert response.status_code == 409
    assert client.get(f"/reminders/{reminder_id}", headers=headers).json()["status"] == "sent"


def test_complete_and_notify_routes_no_longer_exist_d_10():
    headers, task_id = _owner_with_task()
    reminder_id = _create(headers, task_id).json()["id"]

    assert client.post(f"/reminders/{reminder_id}/complete", headers=headers).status_code == 404
    assert client.post(f"/reminders/{reminder_id}/notify", headers=headers).status_code == 404
