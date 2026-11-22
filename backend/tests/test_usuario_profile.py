"""Actualizar nombre y correo de la cuenta (RF-USR-06)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.application.use_cases.manage_account import (
    IncorrectPasswordError,
    UpdateProfileUseCase,
)
from app.modules.usuario.application.use_cases.register_user import RegisterUserUseCase
from tests.helpers import CONSENT, TEST_PASSWORD

client = TestClient(app)
ME = "/users/me"


@pytest.fixture(autouse=True)
def _clean(clean_db) -> None:
    """Cada prueba arranca con las tablas vacías."""


def _register(email: str | None = None) -> str:
    email = email or f"perfil-{uuid.uuid4().hex[:8]}@example.com"
    created = client.post(
        "/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD, **CONSENT}
    )
    assert created.status_code == 201, created.text
    return email


def _headers(email: str) -> dict[str, str]:
    login = client.post("/users/login", json={"email": email, "password": TEST_PASSWORD})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_change_name_returns_200_with_the_updated_profile():
    """RF-USR-06: cambiar el nombre → 200 con el perfil actualizado."""
    headers = _headers(_register())

    response = client.patch(ME, json={"full_name": "  Ana María Pérez  "}, headers=headers)

    assert response.status_code == 200
    assert response.json()["full_name"] == "Ana María Pérez"
    assert client.get(ME, headers=headers).json()["full_name"] == "Ana María Pérez"
    assert "password_hash" not in response.json()


def test_change_email_with_the_current_password_normalizes_it():
    email = _register()
    headers = _headers(email)

    response = client.patch(
        ME, json={"email": " Nuevo.Correo@Example.com ", "current_password": TEST_PASSWORD}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["email"] == "nuevo.correo@example.com"
    login = client.post("/users/login", json={"email": "nuevo.correo@example.com", "password": TEST_PASSWORD})
    assert login.status_code == 200


def test_change_email_to_one_already_used_returns_409():
    """RF-USR-06: cambiar el correo a uno ya usado → 409."""
    taken = _register()
    headers = _headers(_register())

    response = client.patch(ME, json={"email": taken, "current_password": TEST_PASSWORD}, headers=headers)

    assert response.status_code == 409
    assert response.json() == {"detail": "Ya existe un usuario con ese correo."}


@pytest.mark.parametrize("password", [None, "clave-incorrecta"])
def test_change_email_without_password_or_with_a_wrong_one_returns_403(password):
    """RF-USR-06: cambiar el correo sin contraseña o con una incorrecta → 403."""
    email = _register()
    headers = _headers(email)
    body = {"email": f"otro-{uuid.uuid4().hex[:6]}@example.com"}
    if password is not None:
        body["current_password"] = password

    response = client.patch(ME, json=body, headers=headers)

    assert response.status_code == 403
    assert client.get(ME, headers=headers).json()["email"] == email


def test_same_email_does_not_require_the_password():
    email = _register()
    headers = _headers(email)

    response = client.patch(ME, json={"email": email.upper(), "full_name": "Ana"}, headers=headers)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "body",
    [{"full_name": "   "}, {"full_name": "x" * 101}, {"email": "sin-arroba", "current_password": TEST_PASSWORD}],
)
def test_registration_validations_apply_with_422(body):
    """RF-USR-06: aplican las mismas validaciones que en RF-USR-01."""
    headers = _headers(_register())

    response = client.patch(ME, json=body, headers=headers)

    assert response.status_code == 422


def test_update_requires_authentication():
    assert client.patch(ME, json={"full_name": "Ana"}).status_code == 401


def test_use_case_checks_the_password_before_uniqueness():
    """Sin la contraseña no se revela si el otro correo está registrado."""
    users = InMemoryUserRepository()
    hasher = Pbkdf2PasswordHasher()
    register = RegisterUserUseCase(users, hasher)
    register.execute(full_name="Ana", email="ana@example.com", password=TEST_PASSWORD, **CONSENT)
    other = register.execute(full_name="Luis", email="luis@example.com", password=TEST_PASSWORD, **CONSENT)
    use_case = UpdateProfileUseCase(users, hasher)

    with pytest.raises(IncorrectPasswordError):
        use_case.execute(other.id, email="ana@example.com", current_password="clave-incorrecta")
