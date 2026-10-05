"""Pruebas de asignaturas y alias (RF-ASG-01…05, RF-ASG-09)."""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.modules.academic.domain.entities.subject import normalize_text
from tests.helpers import TEST_PASSWORD

client = TestClient(app)


def register_and_login() -> dict:
    email = f"asg-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/users", json={"full_name": "Estudiante", "email": email, "password": TEST_PASSWORD})
    login = client.post("/users/login", json={"email": email, "password": TEST_PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_subject(headers: dict, name: str, teacher: str | None = None) -> dict:
    response = client.post("/academic/subjects", json={"name": name, "teacher": teacher}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_normalize_text_ignores_case_accents_and_spaces():
    assert normalize_text("  Matemáticas   Básicas ") == "matematicas basicas"


def test_create_subject_rf_asg_01():
    headers = register_and_login()

    body = create_subject(headers, "Matemáticas Básicas", "Ana Gómez")

    assert body["name"] == "Matemáticas Básicas"
    assert body["teacher"] == "Ana Gómez"
    assert body["archived"] is False
    assert body["aliases"] == []


def test_duplicate_normalized_name_returns_409():
    headers = register_and_login()
    create_subject(headers, "Matemáticas Básicas")

    response = client.post("/academic/subjects", json={"name": "matematicas  basicas"}, headers=headers)

    assert response.status_code == 409


def test_same_name_is_allowed_for_different_users():
    create_subject(register_and_login(), "Física")
    create_subject(register_and_login(), "Física")


def test_subject_requires_authentication():
    assert client.post("/academic/subjects", json={"name": "Física"}).status_code == 401


def test_list_hides_archived_unless_requested_rf_asg_02_05():
    headers = register_and_login()
    active = create_subject(headers, "Química")
    archived = create_subject(headers, "Historia")
    client.post(f"/academic/subjects/{archived['id']}/archive", headers=headers)

    default = client.get("/academic/subjects", headers=headers).json()
    everything = client.get("/academic/subjects", params={"include_archived": True}, headers=headers).json()

    assert [s["id"] for s in default] == [active["id"]]
    assert {s["id"] for s in everything} == {active["id"], archived["id"]}


def test_other_user_gets_404_rt_02():
    subject = create_subject(register_and_login(), "Cálculo")

    response = client.get(f"/academic/subjects/{subject['id']}", headers=register_and_login())

    assert response.status_code == 404


def test_update_subject_rf_asg_03():
    headers = register_and_login()
    subject = create_subject(headers, "Calculo")

    response = client.patch(
        f"/academic/subjects/{subject['id']}", json={"name": "Cálculo I", "teacher": "Luis"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Cálculo I"
    assert response.json()["teacher"] == "Luis"


def test_rename_to_existing_name_returns_409():
    headers = register_and_login()
    create_subject(headers, "Física")
    other = create_subject(headers, "Química")

    response = client.patch(f"/academic/subjects/{other['id']}", json={"name": "FISICA"}, headers=headers)

    assert response.status_code == 409


def test_delete_subject_removes_its_schedule_blocks_rf_asg_04():
    headers = register_and_login()
    subject = create_subject(headers, "Biología")
    client.post(
        "/academic/schedule-blocks",
        json={"subject_id": subject["id"], "weekday": "monday", "start_time": "08:00", "end_time": "10:00"},
        headers=headers,
    )

    response = client.delete(f"/academic/subjects/{subject['id']}", headers=headers)

    assert response.status_code == 204
    assert client.get(f"/academic/subjects/{subject['id']}", headers=headers).status_code == 404
    assert client.get("/academic/schedule-blocks", headers=headers).json() == []


def test_archive_and_unarchive_rf_asg_05():
    headers = register_and_login()
    subject = create_subject(headers, "Inglés")

    archived = client.post(f"/academic/subjects/{subject['id']}/archive", headers=headers).json()
    restored = client.post(f"/academic/subjects/{subject['id']}/unarchive", headers=headers).json()

    assert archived["archived"] is True
    assert archived["archived_at"] is not None
    assert restored["archived"] is False


def test_unarchive_with_overlapping_schedule_returns_409():
    headers = register_and_login()
    old = create_subject(headers, "Dibujo")
    client.post(
        "/academic/schedule-blocks",
        json={"subject_id": old["id"], "weekday": "monday", "start_time": "08:00", "end_time": "10:00"},
        headers=headers,
    )
    client.post(f"/academic/subjects/{old['id']}/archive", headers=headers)
    new = create_subject(headers, "Diseño")
    client.post(
        "/academic/schedule-blocks",
        json={"subject_id": new["id"], "weekday": "monday", "start_time": "09:00", "end_time": "11:00"},
        headers=headers,
    )

    response = client.post(f"/academic/subjects/{old['id']}/unarchive", headers=headers)

    assert response.status_code == 409


def test_aliases_rf_asg_09():
    headers = register_and_login()
    subject = create_subject(headers, "Matemáticas Básicas")

    added = client.post(f"/academic/subjects/{subject['id']}/aliases", json={"alias": "Mate básicas"}, headers=headers)
    duplicate = client.post(f"/academic/subjects/{subject['id']}/aliases", json={"alias": "mate basicas"}, headers=headers)

    assert added.status_code == 201
    assert [a["alias"] for a in added.json()["aliases"]] == ["Mate básicas"]
    assert duplicate.status_code == 422

    alias_id = added.json()["aliases"][0]["id"]
    removed = client.delete(f"/academic/subjects/{subject['id']}/aliases/{alias_id}", headers=headers)
    assert removed.status_code == 200
    assert removed.json()["aliases"] == []
    missing = client.delete(f"/academic/subjects/{subject['id']}/aliases/{alias_id}", headers=headers)
    assert missing.status_code == 404
