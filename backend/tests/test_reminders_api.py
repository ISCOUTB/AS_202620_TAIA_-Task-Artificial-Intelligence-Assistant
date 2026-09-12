from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def register_and_login(email: str) -> dict[str, str]:
    created = client.post('/users', json={'name': 'Estudiante', 'email': email, 'password': 'password123'})
    assert created.status_code == 201
    login = client.post('/users/login', json={'email': email, 'password': 'password123'})
    assert login.status_code == 200
    return {'Authorization': f"Bearer {login.json()['access_token']}"}


def create_task(headers, title='Tarea vinculada'):
    response = client.post('/academic/tasks', headers=headers, json={'title': title, 'due_date': '2026-09-20'})
    assert response.status_code == 201
    return response.json()['id']


def future_iso(minutes=30):
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def test_reminders_require_authentication():
    response = client.get('/reminders')
    assert response.status_code == 401


def test_create_list_edit_complete_and_delete_reminder():
    headers = register_and_login('reminders-crud@example.com')
    task_id = create_task(headers)

    created = client.post('/reminders', headers=headers, json={
        'message': 'Revisar entrega',
        'scheduled_at': future_iso(),
        'task_id': task_id,
    })
    assert created.status_code == 201
    reminder = created.json()
    assert reminder['message'] == 'Revisar entrega'
    assert reminder['task_id'] == task_id
    reminder_id = reminder['id']

    listed = client.get('/reminders', headers=headers)
    assert listed.status_code == 200
    assert any(item['id'] == reminder_id for item in listed.json())

    edited = client.patch(f'/reminders/{reminder_id}', headers=headers, json={'message': 'Revisar entrega final', 'scheduled_at': future_iso(60)})
    assert edited.status_code == 200
    assert edited.json()['message'] == 'Revisar entrega final'

    completed = client.post(f'/reminders/{reminder_id}/complete', headers=headers)
    assert completed.status_code == 200
    assert completed.json()['is_completed'] is True

    deleted = client.delete(f'/reminders/{reminder_id}', headers=headers)
    assert deleted.status_code == 204

    missing = client.get(f'/reminders/{reminder_id}', headers=headers)
    assert missing.status_code == 404


def test_reminder_cannot_reference_another_users_task():
    owner = register_and_login('reminders-owner@example.com')
    other = register_and_login('reminders-other@example.com')
    task_id = create_task(owner, 'Tarea privada')

    response = client.post('/reminders', headers=other, json={
        'message': 'No debería poder vincularla',
        'scheduled_at': future_iso(),
        'task_id': task_id,
    })
    assert response.status_code == 422
    assert 'no existe o no pertenece' in response.json()['detail']


def test_reminder_cannot_be_accessed_by_another_user():
    owner = register_and_login('reminders-owner-access@example.com')
    other = register_and_login('reminders-other-access@example.com')
    task_id = create_task(owner)
    created = client.post('/reminders', headers=owner, json={
        'message': 'Privado', 'scheduled_at': future_iso(), 'task_id': task_id,
    })
    assert created.status_code == 201
    reminder_id = created.json()['id']

    response = client.get(f'/reminders/{reminder_id}', headers=other)
    assert response.status_code == 404


def test_completed_reminder_cannot_be_edited():
    headers = register_and_login('reminders-completed@example.com')
    task_id = create_task(headers)
    created = client.post('/reminders', headers=headers, json={
        'message': 'No editar después', 'scheduled_at': future_iso(), 'task_id': task_id,
    })
    reminder_id = created.json()['id']
    assert client.post(f'/reminders/{reminder_id}/complete', headers=headers).status_code == 200

    edited = client.patch(f'/reminders/{reminder_id}', headers=headers, json={'message': 'Cambio'})
    assert edited.status_code == 422
