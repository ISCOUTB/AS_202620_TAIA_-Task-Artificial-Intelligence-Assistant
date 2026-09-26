"""Pruebas de la API de tareas y exámenes (RF-TAR-01, 03…10, RF-ASG-02, RF-ASG-04, RT-02)."""

from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.shared.clock import now_bogota
from tests.helpers import create_subject, future_iso, register_and_login

client = TestClient(app)


def _post_task(headers, subject_id, title="Taller", due_at=None, **extra):
    payload = {"subject_id": subject_id, "title": title, "due_at": due_at or future_iso(), **extra}
    return client.post("/academic/tasks", json=payload, headers=headers)


def test_create_task_rf_tar_01():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers, "Cálculo")

    response = _post_task(headers, subject_id, "Taller 3", type="exam", description="Integrales")

    assert response.status_code == 201
    body = response.json()
    assert body["subject_id"] == subject_id
    assert body["subject_name"] == "Cálculo"
    assert body["type"] == "exam"
    assert body["status"] == "pending"
    assert body["completed_at"] is None


def test_task_type_defaults_to_task():
    headers = register_and_login(client)

    assert _post_task(headers, create_subject(client, headers)).json()["type"] == "task"


def test_date_only_due_at_means_2359_bogota_rt_03():
    headers = register_and_login(client)
    day = (now_bogota() + timedelta(days=10)).date().isoformat()

    body = _post_task(headers, create_subject(client, headers), due_at=day).json()

    assert body["due_at"] == f"{day}T23:59:00-05:00"


def test_naive_due_at_is_bogota_time_rt_03():
    headers = register_and_login(client)
    day = (now_bogota() + timedelta(days=10)).date().isoformat()

    body = _post_task(headers, create_subject(client, headers), due_at=f"{day}T21:00:00").json()

    assert body["due_at"] == f"{day}T21:00:00-05:00"


def test_past_due_at_returns_422():
    headers = register_and_login(client)

    response = _post_task(headers, create_subject(client, headers), due_at=(now_bogota() - timedelta(days=1)).isoformat())

    assert response.status_code == 422


def test_subject_of_other_user_returns_404():
    subject_id = create_subject(client, register_and_login(client))

    assert _post_task(register_and_login(client), subject_id).status_code == 404


def test_archived_subject_returns_422():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers)
    client.post(f"/academic/subjects/{subject_id}/archive", headers=headers)

    assert _post_task(headers, subject_id).status_code == 422


def test_task_requires_authentication():
    assert client.get("/academic/tasks").status_code == 401


def test_priority_is_returned_rf_tar_03():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers)

    soon = _post_task(headers, subject_id, due_at=(now_bogota() + timedelta(hours=30)).isoformat()).json()
    later = _post_task(headers, subject_id, due_at=future_iso(days=20)).json()

    assert soon["priority"] == "high"
    assert later["priority"] == "low"


def test_list_is_sorted_filtered_and_paginated_rf_tar_04():
    headers = register_and_login(client)
    physics = create_subject(client, headers, "Física")
    math = create_subject(client, headers, "Matemáticas")
    for days in (9, 3, 6):
        _post_task(headers, physics, f"Física {days}", due_at=future_iso(days=days))
    _post_task(headers, math, "Parcial de derivadas", due_at=future_iso(days=1), type="exam")

    everything = client.get("/academic/tasks", headers=headers).json()
    by_subject = client.get("/academic/tasks", params={"subject_id": physics}, headers=headers).json()
    exams = client.get("/academic/tasks", params={"type": "exam"}, headers=headers).json()
    text = client.get("/academic/tasks", params={"q": "DERIVADAS"}, headers=headers).json()
    page = client.get("/academic/tasks", params={"limit": 2, "offset": 2}, headers=headers).json()

    assert [t["title"] for t in everything["items"]] == ["Parcial de derivadas", "Física 3", "Física 6", "Física 9"]
    assert everything["total"] == 4
    assert [t["title"] for t in by_subject["items"]] == ["Física 3", "Física 6", "Física 9"]
    assert [t["title"] for t in exams["items"]] == ["Parcial de derivadas"]
    assert [t["title"] for t in text["items"]] == ["Parcial de derivadas"]
    assert ([t["title"] for t in page["items"]], page["total"], page["limit"], page["offset"]) == (
        ["Física 6", "Física 9"], 4, 2, 2
    )


def test_default_page_size_is_20():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers)
    for _ in range(25):
        _post_task(headers, subject_id)

    page = client.get("/academic/tasks", headers=headers).json()

    assert len(page["items"]) == 20
    assert page["total"] == 25


def test_filter_by_status_and_due_range():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers)
    done = _post_task(headers, subject_id, "Hecha", due_at=future_iso(days=2)).json()
    _post_task(headers, subject_id, "Pendiente", due_at=future_iso(days=4))
    client.patch(f"/academic/tasks/{done['id']}/complete", headers=headers)

    completed = client.get("/academic/tasks", params={"status": "completed"}, headers=headers).json()
    pending = client.get("/academic/tasks", params={"status": "pending"}, headers=headers).json()
    in_range = client.get(
        "/academic/tasks", params={"due_from": future_iso(days=3), "due_to": future_iso(days=5)}, headers=headers
    ).json()

    assert [t["title"] for t in completed["items"]] == ["Hecha"]
    assert [t["title"] for t in pending["items"]] == ["Pendiente"]
    assert [t["title"] for t in in_range["items"]] == ["Pendiente"]


def test_users_only_see_their_tasks_rt_02():
    owner = register_and_login(client)
    task_id = _post_task(owner, create_subject(client, owner)).json()["id"]
    intruder = register_and_login(client)

    assert client.get("/academic/tasks", headers=intruder).json()["total"] == 0
    assert client.get(f"/academic/tasks/{task_id}", headers=intruder).status_code == 404
    assert client.patch(f"/academic/tasks/{task_id}/complete", headers=intruder).status_code == 404
    assert client.delete(f"/academic/tasks/{task_id}", headers=intruder).status_code == 404


def test_get_task_detail_rf_tar_05():
    headers = register_and_login(client)
    task_id = _post_task(headers, create_subject(client, headers), "Detalle").json()["id"]

    response = client.get(f"/academic/tasks/{task_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["title"] == "Detalle"


def test_update_task_rf_tar_06():
    headers = register_and_login(client)
    first = create_subject(client, headers, "Física")
    second = create_subject(client, headers, "Química")
    task_id = _post_task(headers, first).json()["id"]
    new_due = future_iso(days=12)

    response = client.patch(
        f"/academic/tasks/{task_id}",
        json={"title": "Informe final", "subject_id": second, "due_at": new_due, "type": "exam"},
        headers=headers,
    )

    body = response.json()
    assert response.status_code == 200
    assert (body["title"], body["subject_name"], body["type"]) == ("Informe final", "Química", "exam")


def test_update_to_other_users_subject_returns_404():
    headers = register_and_login(client)
    task_id = _post_task(headers, create_subject(client, headers)).json()["id"]
    foreign = create_subject(client, register_and_login(client))

    response = client.patch(f"/academic/tasks/{task_id}", json={"subject_id": foreign}, headers=headers)

    assert response.status_code == 404


def test_complete_and_reopen_rf_tar_07_08():
    headers = register_and_login(client)
    task_id = _post_task(headers, create_subject(client, headers)).json()["id"]

    first = client.patch(f"/academic/tasks/{task_id}/complete", headers=headers).json()
    second = client.patch(f"/academic/tasks/{task_id}/complete", headers=headers).json()
    reopened = client.patch(f"/academic/tasks/{task_id}/reopen", headers=headers).json()

    assert first["status"] == "completed"
    assert first["completed_at"] is not None
    assert second["completed_at"] == first["completed_at"]
    assert (reopened["status"], reopened["completed_at"]) == ("pending", None)


def test_delete_task_rf_tar_10():
    headers = register_and_login(client)
    task_id = _post_task(headers, create_subject(client, headers)).json()["id"]

    assert client.delete(f"/academic/tasks/{task_id}", headers=headers).status_code == 204
    assert client.get(f"/academic/tasks/{task_id}", headers=headers).status_code == 404
    assert client.get("/academic/tasks", headers=headers).json()["total"] == 0


def test_subject_pending_tasks_count_rf_asg_02():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers)
    ids = [_post_task(headers, subject_id).json()["id"] for _ in range(3)]
    client.patch(f"/academic/tasks/{ids[0]}/complete", headers=headers)
    client.delete(f"/academic/tasks/{ids[1]}", headers=headers)

    assert client.get(f"/academic/subjects/{subject_id}", headers=headers).json()["pending_tasks"] == 1


def test_subject_with_tasks_cannot_be_deleted_rf_asg_04():
    headers = register_and_login(client)
    subject_id = create_subject(client, headers)
    task_id = _post_task(headers, subject_id).json()["id"]
    client.delete(f"/academic/tasks/{task_id}", headers=headers)

    # Aunque la tarea esté eliminada lógicamente, sigue referenciando la asignatura.
    response = client.delete(f"/academic/subjects/{subject_id}", headers=headers)

    assert response.status_code == 409
    assert "archívala" in response.json()["detail"]
