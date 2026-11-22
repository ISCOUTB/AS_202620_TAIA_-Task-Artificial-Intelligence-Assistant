"""Cambiar la contraseña (RF-USR-07)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.usuario.adapters.outbound.in_memory_session_repository import InMemorySessionRepository
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.application.use_cases.manage_account import ChangePasswordUseCase
from app.modules.usuario.application.use_cases.register_user import RegisterUserUseCase
from app.shared.clock import now_bogota
from tests.helpers import CONSENT, TEST_PASSWORD

client = TestClient(app)
PASSWORD_PATH = "/users/me/password"
NEW_PASSWORD = "nueva-clave-segura-2026"


@pytest.fixture(autouse=True)
def _clean(clean_db) -> None:
    """Cada prueba arranca con las tablas vacías."""


def _register() -> str:
    email = f"clave-{uuid.uuid4().hex[:8]}@example.com"
    created = client.post(
        "/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD, **CONSENT}
    )
    assert created.status_code == 201, created.text
    return email


def _login(email: str, password: str = TEST_PASSWORD):
    return client.post("/users/login", json={"email": email, "password": password})


def _headers(email: str) -> dict[str, str]:
    login = _login(email)
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _change(headers: dict[str, str], current: str, new: str):
    return client.put(
        PASSWORD_PATH, json={"current_password": current, "new_password": new}, headers=headers
    )


def test_wrong_current_password_returns_403():
    """RF-USR-07: contraseña actual incorrecta → 403."""
    email = _register()
    headers = _headers(email)

    response = _change(headers, "clave-incorrecta", NEW_PASSWORD)

    assert response.status_code == 403
    assert _login(email).status_code == 200


def test_after_the_change_only_the_new_password_logs_in():
    """RF-USR-07: la contraseña anterior ya no permite iniciar sesión y la nueva sí."""
    email = _register()

    response = _change(_headers(email), TEST_PASSWORD, NEW_PASSWORD)

    assert response.status_code == 204
    assert _login(email).status_code == 401
    assert _login(email, NEW_PASSWORD).status_code == 200


def test_other_sessions_are_revoked_and_the_current_one_stays():
    """RF-USR-07: al cambiarla se revocan todas las demás sesiones."""
    email = _register()
    current = _headers(email)
    other_login = _login(email).json()
    other = {"Authorization": f"Bearer {other_login['access_token']}"}

    assert _change(current, TEST_PASSWORD, NEW_PASSWORD).status_code == 204

    assert client.get("/users/me", headers=current).status_code == 200
    assert client.get("/users/me", headers=other).status_code == 401
    refreshed = client.post("/users/refresh", json={"refresh_token": other_login["refresh_token"]})
    assert refreshed.status_code == 401


@pytest.mark.parametrize(
    ("new_password", "detail"),
    [
        ("corta", "La contraseña debe tener al menos 8 caracteres."),
        (TEST_PASSWORD, "La nueva contraseña debe ser distinta de la actual."),
    ],
)
def test_new_password_must_follow_the_rules_and_differ(new_password, detail):
    """RF-USR-07: la nueva cumple RF-USR-01 y es distinta de la actual."""
    email = _register()

    response = _change(_headers(email), TEST_PASSWORD, new_password)

    assert response.status_code == 422
    assert response.json() == {"detail": detail}
    assert _login(email).status_code == 200


def test_change_password_requires_authentication():
    response = client.put(
        PASSWORD_PATH, json={"current_password": TEST_PASSWORD, "new_password": NEW_PASSWORD}
    )

    assert response.status_code == 401


def test_use_case_revokes_only_the_other_sessions_in_memory():
    """RF-USR-07 sobre los dobles en memoria."""
    users, sessions, hasher = InMemoryUserRepository(), InMemorySessionRepository(), Pbkdf2PasswordHasher()
    user = RegisterUserUseCase(users, hasher).execute(
        full_name="Ana", email="ana@example.com", password=TEST_PASSWORD, **CONSENT
    )
    current, other = uuid.uuid4(), uuid.uuid4()
    sessions.create(current, user.id, "refresh-actual", now_bogota())
    sessions.create(other, user.id, "refresh-otro", now_bogota())

    ChangePasswordUseCase(users, hasher, sessions).execute(user.id, current, TEST_PASSWORD, NEW_PASSWORD)

    assert sessions.is_active(current)
    assert not sessions.is_active(other)
    assert hasher.verify(NEW_PASSWORD, users.get_by_id(user.id).password_hash)
