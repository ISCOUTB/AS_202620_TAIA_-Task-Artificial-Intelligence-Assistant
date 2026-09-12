from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def login_user(email: str) -> dict[str, str]:
    response = client.post(
        "/users",
        json={"name": email, "email": email, "password": "password123"},
    )
    assert response.status_code == 201
    login = client.post(
        "/users/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_authenticated_user_can_complete_own_task():
    headers = login_user("academic-complete@example.com")
    created = client.post(
        "/academic/tasks",
        json={"title": "Estudiar arquitectura", "due_date": "2026-09-15"},
        headers=headers,
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    response = client.patch(f"/academic/tasks/{task_id}/complete", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_user_cannot_complete_another_users_task():
    owner = login_user("academic-owner@example.com")
    other = login_user("academic-other@example.com")

    created = client.post(
        "/academic/tasks",
        json={"title": "Tarea privada", "due_date": "2026-09-15"},
        headers=owner,
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    response = client.patch(f"/academic/tasks/{task_id}/complete", headers=other)

    assert response.status_code == 404


def test_complete_task_requires_authentication():
    response = client.patch(
        "/academic/tasks/00000000-0000-0000-0000-000000000000/complete"
    )

    assert response.status_code == 401
