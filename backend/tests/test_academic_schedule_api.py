"""Pruebas del horario de clases y del período académico (RF-ASG-06…08)."""

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_and_login() -> dict:
    email = f"hor-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/users", json={"full_name": "Estudiante", "email": email, "password": "password123"})
    login = client.post("/users/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_subject(headers: dict, name: str) -> str:
    return client.post("/academic/subjects", json={"name": name}, headers=headers).json()["id"]


def create_block(headers: dict, subject_id: str, weekday: str, start: str, end: str, room: str | None = None):
    return client.post(
        "/academic/schedule-blocks",
        json={"subject_id": subject_id, "weekday": weekday, "start_time": start, "end_time": end, "room": room},
        headers=headers,
    )


def test_create_block_rf_asg_06():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")

    response = create_block(headers, subject_id, "monday", "08:00", "10:00", "A-201")

    assert response.status_code == 201
    body = response.json()
    assert body["subject_name"] == "Física"
    assert body["weekday"] == "monday"
    assert body["start_time"] == "08:00:00"
    assert body["room"] == "A-201"


def test_overlapping_block_returns_409():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")
    create_block(headers, subject_id, "monday", "08:00", "10:00")

    response = create_block(headers, subject_id, "monday", "09:00", "11:00")

    assert response.status_code == 409


def test_adjacent_blocks_do_not_overlap():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")
    create_block(headers, subject_id, "monday", "08:00", "10:00")

    assert create_block(headers, subject_id, "monday", "10:00", "12:00").status_code == 201


def test_end_before_start_returns_422():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")

    assert create_block(headers, subject_id, "monday", "10:00", "08:00").status_code == 422


def test_block_for_archived_subject_returns_422():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")
    client.post(f"/academic/subjects/{subject_id}/archive", headers=headers)

    assert create_block(headers, subject_id, "monday", "08:00", "10:00").status_code == 422


def test_block_for_other_users_subject_returns_404():
    subject_id = create_subject(register_and_login(), "Física")

    assert create_block(register_and_login(), subject_id, "monday", "08:00", "10:00").status_code == 404


def test_weekly_schedule_is_sorted_and_filterable_rf_asg_07():
    headers = register_and_login()
    physics = create_subject(headers, "Física")
    math = create_subject(headers, "Matemáticas")
    create_block(headers, math, "wednesday", "14:00", "16:00")
    create_block(headers, physics, "monday", "10:00", "12:00")
    create_block(headers, math, "monday", "07:00", "09:00")

    week = client.get("/academic/schedule-blocks", headers=headers).json()
    wednesday = client.get("/academic/schedule-blocks", params={"weekday": "wednesday"}, headers=headers).json()

    assert [(b["weekday"], b["start_time"]) for b in week] == [
        ("monday", "07:00:00"),
        ("monday", "10:00:00"),
        ("wednesday", "14:00:00"),
    ]
    assert [b["subject_name"] for b in wednesday] == ["Matemáticas"]


def test_archived_subject_blocks_are_hidden_rf_asg_05():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")
    create_block(headers, subject_id, "friday", "08:00", "10:00")
    client.post(f"/academic/subjects/{subject_id}/archive", headers=headers)

    assert client.get("/academic/schedule-blocks", headers=headers).json() == []


def test_update_and_delete_block():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")
    block = create_block(headers, subject_id, "monday", "08:00", "10:00").json()

    updated = client.patch(
        f"/academic/schedule-blocks/{block['id']}", json={"weekday": "tuesday", "end_time": "11:00"}, headers=headers
    )
    deleted = client.delete(f"/academic/schedule-blocks/{block['id']}", headers=headers)

    assert updated.status_code == 200
    assert updated.json()["weekday"] == "tuesday"
    assert updated.json()["end_time"] == "11:00:00"
    assert deleted.status_code == 204
    assert client.get("/academic/schedule-blocks", headers=headers).json() == []


def test_failed_update_does_not_change_block():
    headers = register_and_login()
    subject_id = create_subject(headers, "Física")
    create_block(headers, subject_id, "monday", "08:00", "10:00")
    other = create_block(headers, subject_id, "monday", "10:00", "12:00").json()

    response = client.patch(f"/academic/schedule-blocks/{other['id']}", json={"start_time": "09:00"}, headers=headers)

    assert response.status_code == 409
    starts = [b["start_time"] for b in client.get("/academic/schedule-blocks", headers=headers).json()]
    assert starts == ["08:00:00", "10:00:00"]


def test_other_user_cannot_edit_block():
    owner = register_and_login()
    block = create_block(owner, create_subject(owner, "Física"), "monday", "08:00", "10:00").json()

    response = client.patch(f"/academic/schedule-blocks/{block['id']}", json={"room": "B"}, headers=register_and_login())

    assert response.status_code == 404


def test_academic_period_rf_asg_08():
    headers = register_and_login()

    assert client.get("/academic/period", headers=headers).status_code == 404
    saved = client.put("/academic/period", json={"start_date": "2026-08-01", "end_date": "2026-12-05"}, headers=headers)
    invalid = client.put("/academic/period", json={"start_date": "2026-12-05", "end_date": "2026-08-01"}, headers=headers)

    assert saved.status_code == 200
    assert client.get("/academic/period", headers=headers).json() == {"start_date": "2026-08-01", "end_date": "2026-12-05"}
    assert invalid.status_code == 422
