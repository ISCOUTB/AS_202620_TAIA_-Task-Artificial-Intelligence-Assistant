"""Límite de intentos de inicio de sesión (RNF-03, RF-USR-02)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.usuario.adapters.outbound.in_memory_failed_login_attempt_repository import (
    InMemoryFailedLoginAttemptRepository,
)
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.adapters.outbound.sqlalchemy_failed_login_attempt_repository import (
    SqlAlchemyFailedLoginAttemptRepository,
)
from app.modules.usuario.application.use_cases.login_user import (
    InvalidCredentialsError,
    LoginUserUseCase,
    TooManyLoginAttemptsError,
)
from app.modules.usuario.application.use_cases.register_user import RegisterUserUseCase
from app.shared.clock import BOGOTA_TZ
from tests.helpers import TEST_PASSWORD

EMAIL = "limite@example.com"
WRONG_PASSWORD = "contrasena-incorrecta"
START = datetime(2026, 10, 30, 8, 0, tzinfo=BOGOTA_TZ)


class _Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock():
    return _Clock()


@pytest.fixture
def login(clock):
    users = InMemoryUserRepository()
    hasher = Pbkdf2PasswordHasher()
    RegisterUserUseCase(users, hasher).execute(full_name="Ana", email=EMAIL, password=TEST_PASSWORD)
    return LoginUserUseCase(
        users,
        hasher,
        JwtTokenService(secret="secreto-de-prueba-suficientemente-largo"),
        InMemoryFailedLoginAttemptRepository(),
        now=clock,
    )


def _fail(login, times: int, email: str = EMAIL) -> None:
    for _ in range(times):
        with pytest.raises(InvalidCredentialsError):
            login.execute(email, WRONG_PASSWORD)


def test_sixth_attempt_is_rejected_even_with_the_correct_password(login):
    """RNF-03: 5 fallos por identificador en 15 minutos bloquean el correo."""
    _fail(login, 5)

    with pytest.raises(TooManyLoginAttemptsError):
        login.execute(EMAIL, TEST_PASSWORD)


def test_four_failures_still_allow_login(login):
    _fail(login, 4)

    assert login.execute(EMAIL, TEST_PASSWORD)


def test_limit_expires_after_the_window(login, clock):
    _fail(login, 5)
    clock.now = START + timedelta(minutes=15, seconds=1)

    assert login.execute(EMAIL, TEST_PASSWORD)


def test_limit_is_per_identifier_and_normalized(login):
    """El límite cuenta por correo normalizado y no afecta a otros correos."""
    _fail(login, 5, email="  LIMITE@Example.com ")

    with pytest.raises(TooManyLoginAttemptsError):
        login.execute(EMAIL, TEST_PASSWORD)
    with pytest.raises(InvalidCredentialsError):
        login.execute("otro@example.com", WRONG_PASSWORD)


def test_unregistered_email_is_limited_too(login):
    """Bloquear solo cuentas existentes revelaría cuáles existen (RF-USR-02)."""
    _fail(login, 5, email="nadie@example.com")

    with pytest.raises(TooManyLoginAttemptsError):
        login.execute("nadie@example.com", WRONG_PASSWORD)


def test_login_api_returns_429_after_five_failures():
    client = TestClient(app)
    email = f"api-limite-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD})
    for _ in range(5):
        response = client.post("/users/login", json={"email": email, "password": WRONG_PASSWORD})
        assert response.status_code == 401

    response = client.post("/users/login", json={"email": email, "password": TEST_PASSWORD})

    assert response.status_code == 429
    assert response.json() == {"detail": "Demasiados intentos fallidos. Intenta de nuevo en 15 minutos."}


def test_sqlalchemy_repository_counts_window_and_purges_after_retention(clean_db):
    repository = SqlAlchemyFailedLoginAttemptRepository(clean_db)
    repository.add(EMAIL, START)
    repository.add(EMAIL, START + timedelta(minutes=10))
    repository.add("otro@example.com", START + timedelta(minutes=10))

    assert repository.count_since(EMAIL, START) == 2
    assert repository.count_since(EMAIL, START + timedelta(minutes=5)) == 1

    # Un intento 24 horas después elimina los anteriores a la retención (diccionario 5.6).
    repository.add(EMAIL, START + timedelta(hours=24, minutes=6))
    assert repository.count_since(EMAIL, START - timedelta(days=1)) == 2
