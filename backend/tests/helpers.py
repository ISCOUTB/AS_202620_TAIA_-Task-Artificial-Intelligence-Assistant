"""Ayudantes compartidos por las pruebas de API."""

from __future__ import annotations

import uuid
from datetime import timedelta

from app.shared.clock import now_bogota


def register_and_login(client, email: str | None = None) -> dict[str, str]:
    email = email or f"user-{uuid.uuid4().hex[:10]}@example.com"
    created = client.post("/users", json={"full_name": "Estudiante", "email": email, "password": "password123"})
    assert created.status_code == 201, created.text
    login = client.post("/users/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_subject(client, headers: dict[str, str], name: str = "Programación") -> str:
    response = client.post("/academic/subjects", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def future_iso(days: float = 7) -> str:
    return (now_bogota() + timedelta(days=days)).isoformat()


def create_task(client, headers: dict[str, str], title: str = "Tarea", subject: str = "Programación", **extra) -> str:
    subject_id = extra.pop("subject_id", None) or create_subject(client, headers, f"{subject} {uuid.uuid4().hex[:6]}")
    payload = {"subject_id": subject_id, "title": title, "due_at": future_iso(), **extra}
    response = client.post("/academic/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]
