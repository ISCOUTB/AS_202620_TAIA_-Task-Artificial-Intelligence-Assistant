"""Pruebas del corte vertical del aspecto A-01: registrar y consultar tareas."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_register_task_returns_created_task():
    payload = {
        "title": "Entregar proyecto de programación",
        "due_date": "2026-09-07",
        "subject": "Programación",
    }

    response = client.post("/academic/tasks", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["subject"] == payload["subject"]
    assert body["status"] == "pending"
    assert "id" in body


def test_register_task_rejects_empty_title():
    payload = {"title": "   ", "due_date": "2026-09-07"}

    response = client.post("/academic/tasks", json=payload)

    assert response.status_code == 422


def test_list_tasks_includes_previously_registered_task():
    create_response = client.post(
        "/academic/tasks",
        json={"title": "Estudiar para el parcial", "due_date": "2026-09-10"},
    )
    created_id = create_response.json()["id"]

    list_response = client.get("/academic/tasks")

    assert list_response.status_code == 200
    ids = [task["id"] for task in list_response.json()]
    assert created_id in ids
