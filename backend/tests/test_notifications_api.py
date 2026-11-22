"""API de la bandeja de notificaciones: RF-NOT-03, RT-01 y RT-02."""

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.modules.reminders.domain.entities import Notification
from app.shared.clock import now_bogota
from tests import helpers

client = TestClient(app)


def _user_with_notifications(count: int) -> tuple[dict[str, str], list[str]]:
    """Crea `count` notificaciones, de la más antigua a la más reciente, y devuelve sus ids."""

    headers = helpers.register_and_login(client)
    task_id = helpers.create_task(client, headers, "Informe")
    base = now_bogota()
    ids = []
    for index in range(count):
        reminder = client.post("/reminders", headers=headers, json={
            "task_id": task_id, "scheduled_at": (base + timedelta(hours=index + 1)).isoformat()})
        assert reminder.status_code == 201, reminder.text
        reminder_id = uuid.UUID(reminder.json()["id"])
        notification = Notification(id=uuid.uuid4(), reminder_id=reminder_id, message=f"Recuerda {index}",
                                    created_at=base + timedelta(minutes=index))
        assert main.reminder_repository.claim(reminder_id, notification)
        ids.append(str(notification.id))
    return headers, ids


def test_inbox_requires_authentication_rt_01():
    assert client.get("/notifications").status_code == 401
    assert client.get("/notifications/unread-count").status_code == 401
    assert client.patch("/notifications/read-all").status_code == 401
    assert client.patch(f"/notifications/{uuid.uuid4()}/read").status_code == 401


def test_lists_newest_first_with_pagination_rf_not_03():
    headers, ids = _user_with_notifications(3)

    first = client.get("/notifications", headers=headers, params={"limit": 2, "offset": 0})
    second = client.get("/notifications", headers=headers, params={"limit": 2, "offset": 2})

    assert first.status_code == 200, first.text
    body = first.json()
    assert (body["total"], body["limit"], body["offset"]) == (3, 2, 0)
    assert [item["id"] for item in body["items"]] == [ids[2], ids[1]]
    assert set(body["items"][0]) == {"id", "reminder_id", "message", "created_at", "read_at", "read"}
    assert [item["id"] for item in second.json()["items"]] == [ids[0]]


def test_marks_one_as_read_rf_not_03():
    headers, ids = _user_with_notifications(2)

    response = client.patch(f"/notifications/{ids[0]}/read", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["read"] is True and response.json()["read_at"] is not None
    assert client.get("/notifications/unread-count", headers=headers).json() == {"unread_count": 1}


def test_marks_all_as_read_rf_not_03():
    headers, _ = _user_with_notifications(2)
    assert client.get("/notifications/unread-count", headers=headers).json() == {"unread_count": 2}

    response = client.patch("/notifications/read-all", headers=headers)

    assert response.status_code == 204
    assert client.get("/notifications/unread-count", headers=headers).json() == {"unread_count": 0}
    assert all(item["read"] for item in client.get("/notifications", headers=headers).json()["items"])


def test_another_users_notification_is_not_found_rt_02():
    owner, ids = _user_with_notifications(1)
    other = helpers.register_and_login(client)

    response = client.patch(f"/notifications/{ids[0]}/read", headers=other)

    assert response.status_code == 404
    assert "detail" in response.json()
    assert client.get("/notifications", headers=other).json()["total"] == 0
    client.patch("/notifications/read-all", headers=other)
    assert client.get("/notifications/unread-count", headers=owner).json() == {"unread_count": 1}


def test_unknown_notification_is_not_found_rf_not_03():
    headers = helpers.register_and_login(client)

    assert client.patch(f"/notifications/{uuid.uuid4()}/read", headers=headers).status_code == 404
