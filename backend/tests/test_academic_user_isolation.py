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


def test_user_only_sees_own_academic_tasks():
    user_a = login_user("academic-a@example.com")
    user_b = login_user("academic-b@example.com")

    created = client.post(
        "/academic/tasks",
        json={"title": "Tarea de A", "due_date": "2026-09-10"},
        headers=user_a,
    )
    assert created.status_code == 201

    tasks_a = client.get("/academic/tasks", headers=user_a)
    tasks_b = client.get("/academic/tasks", headers=user_b)

    assert tasks_a.status_code == 200
    assert tasks_b.status_code == 200
    assert [task["title"] for task in tasks_a.json()] == ["Tarea de A"]
    assert tasks_b.json() == []
