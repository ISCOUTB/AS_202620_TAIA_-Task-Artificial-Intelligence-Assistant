from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def register_and_login(email: str):
    register = client.post(
        "/users",
        json={"name": "Estudiante", "email": email, "password": "password123"},
    )
    assert register.status_code == 201
    login = client.post(
        "/users/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_register_task_returns_created_task_for_authenticated_user():
    headers = register_and_login("academic-register@example.com")
    payload = {
        "title": "Entregar proyecto de programación",
        "due_date": "2026-09-07",
        "subject": "Programación",
    }

    response = client.post("/academic/tasks", json=payload, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["subject"] == payload["subject"]
    assert body["status"] == "pending"
    assert "id" in body


def test_register_task_requires_authentication():
    response = client.post(
        "/academic/tasks",
        json={"title": "Sin autenticación", "due_date": "2026-09-07"},
    )

    assert response.status_code == 401
