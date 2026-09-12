from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.modules.reminders.adapters.inbound.http_controller import get_send_notification_use_case
from backend.app.modules.reminders.application.ports.inbound.reminder_ports import SendNotificationPort

client = TestClient(app)


def register_and_login(email: str) -> dict[str, str]:
    created = client.post('/users', json={'name': 'Estudiante', 'email': email, 'password': 'password123'})
    assert created.status_code == 201
    login = client.post('/users/login', json={'email': email, 'password': 'password123'})
    assert login.status_code == 200
    return {'Authorization': f"Bearer {login.json()['access_token']}"}


def create_task(headers):
    response = client.post('/academic/tasks', headers=headers, json={'title': 'Tarea', 'due_date': '2026-09-20'})
    assert response.status_code == 201
    return response.json()['id']


class FakeSender(SendNotificationPort):
    def execute(self, notification):
        return True


def test_notify_requires_ownership_and_sends(monkeypatch):
    owner = register_and_login('notify-owner@example.com')
    other = register_and_login('notify-other@example.com')
    task_id = create_task(owner)
    scheduled = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    created = client.post('/reminders', headers=owner, json={'message': 'Recordatorio', 'scheduled_at': scheduled, 'task_id': task_id})
    assert created.status_code == 201
    reminder_id = created.json()['id']

    app.dependency_overrides[get_send_notification_use_case] = lambda: FakeSender()
    try:
        denied = client.post(f'/reminders/{reminder_id}/notify', headers=other)
        assert denied.status_code == 404

        sent = client.post(f'/reminders/{reminder_id}/notify', headers=owner)
        assert sent.status_code == 200
        assert sent.json()['sent'] is True
    finally:
        app.dependency_overrides.pop(get_send_notification_use_case, None)
