"""Pruebas de la autorización de tratamiento de datos (RF-USR-10, T-02)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.usuario.adapters.outbound.provider import password_hasher, repository
from app.modules.usuario.application.use_cases.register_user import CURRENT_POLICY_VERSION
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from tests.helpers import CONSENT, TEST_PASSWORD

client = TestClient(app)

EMAIL = "consentimiento@example.com"


@pytest.fixture(autouse=True)
def _base_de_datos_limpia(clean_db) -> None:
    """Cada prueba arranca con las tablas vacías: el repositorio ya es SQLAlchemy."""


def _payload(**overrides):
    base = {"full_name": "Ana", "email": EMAIL, "password": TEST_PASSWORD, **CONSENT}
    base.update(overrides)
    return base


def test_registration_without_consent_fields_is_rejected():
    payload = {"full_name": "Ana", "email": EMAIL, "password": TEST_PASSWORD}

    response = client.post("/users", json=payload)

    assert response.status_code == 422


def test_registration_with_consent_false_is_rejected():
    response = client.post("/users", json=_payload(consent_accepted=False))

    assert response.status_code == 422
    assert "política" in response.json()["detail"]


def test_registration_with_an_outdated_policy_version_is_rejected():
    response = client.post("/users", json=_payload(consent_policy_version="2020-01-v0"))

    assert response.status_code == 422
    assert CURRENT_POLICY_VERSION in response.json()["detail"]


def test_rejected_registration_does_not_create_the_account():
    assert client.post("/users", json=_payload(consent_accepted=False)).status_code == 422

    login = client.post("/users/login", json={"email": EMAIL, "password": TEST_PASSWORD})

    assert login.status_code == 401


def test_registration_stores_the_acceptance_date_and_version():
    response = client.post("/users", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["consent_accepted_at"] is not None
    assert body["consent_policy_version"] == CURRENT_POLICY_VERSION

    login = client.post("/users/login", json={"email": EMAIL, "password": TEST_PASSWORD})
    assert login.status_code == 200
    profile = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["consent_policy_version"] == CURRENT_POLICY_VERSION
    assert profile.json()["consent_accepted_at"] is not None


def test_account_created_before_the_policy_can_still_log_in(clean_db):
    # RF-USR-10 no se aplica hacia atrás: las cuentas previas no tienen constancia.
    user = Usuario.create(
        full_name="Cuenta previa",
        email=Email("previa@example.com"),
        password_hash=password_hasher.hash(TEST_PASSWORD),
    )
    repository.add(user)

    response = client.post(
        "/users/login", json={"email": "previa@example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 200
