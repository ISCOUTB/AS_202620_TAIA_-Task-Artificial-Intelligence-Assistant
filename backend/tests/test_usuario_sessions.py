"""Sesiones revocables: renovación con rotación y cierre de sesión (T-08, RF-USR-03, 04)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.modules.usuario.adapters.outbound.in_memory_failed_login_attempt_repository import (
    InMemoryFailedLoginAttemptRepository,
)
from app.modules.usuario.adapters.outbound.in_memory_session_repository import InMemorySessionRepository
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.adapters.outbound.sqlalchemy_session_repository import SqlAlchemySessionRepository
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.usuario.application.use_cases.login_user import LoginUserUseCase
from app.modules.usuario.application.use_cases.manage_sessions import (
    AuthenticateAccessTokenUseCase,
    InvalidRefreshTokenError,
    LogoutUseCase,
    RefreshSessionUseCase,
    RevokedSessionError,
)
from app.modules.usuario.application.use_cases.register_user import RegisterUserUseCase
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import BOGOTA_TZ
from tests.helpers import CONSENT, TEST_PASSWORD

EMAIL = "sesion@example.com"
SECRET = "secreto-de-prueba-suficientemente-largo"
START = datetime(2026, 11, 1, 8, 0, tzinfo=BOGOTA_TZ)


class _Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now


class _Auth:
    """Casos de uso de sesión sobre adaptadores en memoria."""

    def __init__(self) -> None:
        self.clock = _Clock()
        self.users = InMemoryUserRepository()
        self.sessions = InMemorySessionRepository()
        self.tokens = JwtTokenService(secret=SECRET)
        hasher = Pbkdf2PasswordHasher()
        RegisterUserUseCase(self.users, hasher).execute(full_name="Ana", email=EMAIL, password=TEST_PASSWORD)
        self.login = LoginUserUseCase(
            self.users, hasher, self.tokens, InMemoryFailedLoginAttemptRepository(), self.sessions, now=self.clock
        )
        self.refresh = RefreshSessionUseCase(self.users, self.sessions, self.tokens, now=self.clock)
        self.authenticate = AuthenticateAccessTokenUseCase(self.tokens, self.sessions)
        self.logout = LogoutUseCase(self.sessions, now=self.clock)


@pytest.fixture
def auth() -> _Auth:
    return _Auth()


def test_access_token_carries_the_session_id(auth):
    pair = auth.login.execute(EMAIL, TEST_PASSWORD)

    claims = auth.authenticate.execute(pair.access_token)

    assert jwt.decode(pair.access_token, SECRET, algorithms=["HS256"])["sid"] == str(claims.session_id)


def test_token_without_sid_is_rejected(auth):
    """Un JWT sin sesión no se puede revocar, así que no se acepta."""
    user = auth.users.get_by_email(Email(EMAIL))
    legacy = jwt.encode(
        {"sub": str(user.id), "exp": START + timedelta(days=1)}, SECRET, algorithm="HS256"
    )

    with pytest.raises(ValueError):
        auth.authenticate.execute(legacy)


def test_refresh_rotates_and_the_old_token_stops_working(auth):
    first = auth.login.execute(EMAIL, TEST_PASSWORD)

    second = auth.refresh.execute(first.refresh_token)

    assert second.refresh_token != first.refresh_token
    assert auth.authenticate.execute(second.access_token)
    with pytest.raises(InvalidRefreshTokenError):
        auth.refresh.execute(first.refresh_token)


def test_reusing_a_rotated_token_revokes_every_session(auth):
    """RF-USR-03: usar un token ya revocado indica robo y cierra todas las sesiones."""
    stolen = auth.login.execute(EMAIL, TEST_PASSWORD)
    other_device = auth.login.execute(EMAIL, TEST_PASSWORD)
    rotated = auth.refresh.execute(stolen.refresh_token)

    with pytest.raises(InvalidRefreshTokenError):
        auth.refresh.execute(stolen.refresh_token)

    for pair in (rotated, other_device):
        with pytest.raises(RevokedSessionError):
            auth.authenticate.execute(pair.access_token)
        with pytest.raises(InvalidRefreshTokenError):
            auth.refresh.execute(pair.refresh_token)


def test_expired_refresh_token_is_rejected(auth):
    pair = auth.login.execute(EMAIL, TEST_PASSWORD)
    auth.clock.now = START + timedelta(days=30)

    with pytest.raises(InvalidRefreshTokenError):
        auth.refresh.execute(pair.refresh_token)


def test_unknown_refresh_token_is_rejected(auth):
    with pytest.raises(InvalidRefreshTokenError):
        auth.refresh.execute("token-inventado")


def test_logout_invalidates_access_and_refresh_tokens(auth):
    pair = auth.login.execute(EMAIL, TEST_PASSWORD)
    other_device = auth.login.execute(EMAIL, TEST_PASSWORD)

    auth.logout.execute(auth.authenticate.execute(pair.access_token).session_id)

    with pytest.raises(RevokedSessionError):
        auth.authenticate.execute(pair.access_token)
    with pytest.raises(InvalidRefreshTokenError):
        auth.refresh.execute(pair.refresh_token)
    # Solo se cierra la sesión actual.
    assert auth.authenticate.execute(other_device.access_token)


# --- Integración con PostgreSQL y la API ---------------------------------------------


def _login(client: TestClient) -> dict:
    email = f"sesion-{uuid.uuid4().hex[:8]}@example.com"
    created = client.post(
        "/users",
        json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD, **CONSENT},
    )
    assert created.status_code == 201, created.text
    login = client.post("/users/login", json={"email": email, "password": TEST_PASSWORD})
    assert login.status_code == 200, login.text
    return login.json()


def test_api_logout_returns_401_for_the_same_tokens(clean_db):
    """RF-USR-04: tras cerrar sesión, el token de acceso y el de renovación responden 401."""
    client = TestClient(app)
    tokens = _login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    assert client.post("/users/logout", headers=headers).status_code == 204

    assert client.get("/users/me", headers=headers).status_code == 401
    assert client.get("/academic/subjects", headers=headers).status_code == 401
    refreshed = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 401


def test_api_refresh_returns_new_pair_and_rejects_reuse(clean_db):
    """RF-USR-03: renovar entrega un par nuevo; el token anterior ya no sirve."""
    client = TestClient(app)
    tokens = _login(client)

    refreshed = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert client.get("/users/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}).status_code == 200

    reused = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401
    # La reutilización revocó también la sesión renovada.
    assert client.get("/users/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}).status_code == 401


def test_sqlalchemy_repository_stores_only_the_hash(clean_db):
    users = SqlAlchemyUserRepository(clean_db)
    RegisterUserUseCase(users, Pbkdf2PasswordHasher()).execute(full_name="Ana", email=EMAIL, password=TEST_PASSWORD)
    user = users.get_by_email(Email(EMAIL))
    sessions = SqlAlchemySessionRepository(clean_db)
    session_id = uuid.uuid4()
    sessions.create(session_id, user.id, "token-en-claro", START + timedelta(days=30))

    with clean_db() as db:
        stored = db.scalar(text("SELECT token_hash FROM refresh_tokens"))
    assert stored != "token-en-claro" and len(stored) == 64

    assert sessions.rotate_refresh_token("token-en-claro", "siguiente", START + timedelta(days=30), START)
    assert not sessions.rotate_refresh_token("token-en-claro", "otro", START + timedelta(days=30), START)
    assert sessions.get_refresh_token("token-en-claro").used

    sessions.revoke(session_id, START)
    assert not sessions.is_active(session_id)
    assert sessions.get_refresh_token("siguiente").session_revoked
