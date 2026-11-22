"""Desactivar la cuenta y reactivarla iniciando sesión (RF-USR-09, RF-USR-02)."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.reminders.application.ports.inbound import task_reminder_sync as reminder_port
from app.modules.usuario.adapters.outbound.in_memory_failed_login_attempt_repository import (
    InMemoryFailedLoginAttemptRepository,
)
from app.modules.usuario.adapters.outbound.in_memory_session_repository import InMemorySessionRepository
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.adapters.outbound.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.usuario.application.ports.inbound.identity import get_identity_service
from app.modules.usuario.application.ports.inbound.user_devices import get_user_device_directory
from app.modules.usuario.application.use_cases.login_user import InactiveUserError, LoginUserUseCase
from app.modules.usuario.application.use_cases.manage_account import (
    DeactivateAccountUseCase,
    IncorrectPasswordError,
)
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import now_bogota
from tests.helpers import CONSENT, TEST_PASSWORD

client = TestClient(app)
DEACTIVATE_PATH = "/users/me/deactivate"
TELEGRAM_USER_ID = 987654321


class RecordingReminderSync:
    """Doble de `TaskReminderSync` que solo registra las cuentas canceladas."""

    def __init__(self) -> None:
        self.cancelled_users: list[uuid.UUID] = []

    def cancel_all_for_user(self, user_id: uuid.UUID) -> None:
        self.cancelled_users.append(user_id)


@pytest.fixture(autouse=True)
def reminder_sync(clean_db, monkeypatch) -> RecordingReminderSync:
    """Cada prueba arranca con las tablas vacías y un doble de Reminders configurado."""
    monkeypatch.setattr(reminder_port, "_service", reminder_port._service)
    recorder = RecordingReminderSync()
    reminder_port.configure_task_reminder_sync(recorder)
    return recorder


def _register() -> str:
    email = f"baja-{uuid.uuid4().hex[:8]}@example.com"
    created = client.post(
        "/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD, **CONSENT}
    )
    assert created.status_code == 201, created.text
    return email


def _login(email: str):
    return client.post("/users/login", json={"email": email, "password": TEST_PASSWORD})


def _tokens(email: str) -> dict[str, str]:
    login = _login(email)
    assert login.status_code == 200, login.text
    return login.json()


def _headers(tokens: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _user_id(tokens: dict[str, str]) -> uuid.UUID:
    return uuid.UUID(client.get("/users/me", headers=_headers(tokens)).json()["id"])


def _deactivate(tokens: dict[str, str], password: str = TEST_PASSWORD):
    return client.post(DEACTIVATE_PATH, json={"current_password": password}, headers=_headers(tokens))


def _move_deactivation_back(clean_db, user_id: uuid.UUID, days: int) -> None:
    users = SqlAlchemyUserRepository(clean_db)
    user = users.get_by_id(user_id)
    user.deactivated_at = now_bogota() - timedelta(days=days)
    users.save(user)


def test_previous_tokens_get_401_after_deactivating():
    """RF-USR-09: después de desactivar, usar un token previo → 401."""
    tokens = _tokens(_register())

    response = _deactivate(tokens)

    assert response.status_code == 204
    assert client.get("/users/me", headers=_headers(tokens)).status_code == 401
    refreshed = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 401


def test_deactivation_requires_the_current_password():
    """RF-USR-09: exige la contraseña actual; con una incorrecta → 403 y la cuenta sigue activa."""
    tokens = _tokens(_register())

    response = _deactivate(tokens, "clave-incorrecta")

    assert response.status_code == 403
    assert client.get("/users/me", headers=_headers(tokens)).status_code == 200


def test_deactivation_cuts_every_channel(clean_db, reminder_sync):
    """RF-USR-09: se revocan las sesiones, se desvincula Telegram, se quitan los dispositivos
    y se cancelan los recordatorios pendientes."""
    email = _register()
    tokens, other = _tokens(email), _tokens(email)
    client.put("/users/me/fcm-token", json={"fcm_token": "token-a"}, headers=_headers(other))
    user_id = _user_id(tokens)
    users = SqlAlchemyUserRepository(clean_db)
    user = users.get_by_id(user_id)
    user.link_telegram(TELEGRAM_USER_ID)
    users.save(user)

    assert _deactivate(tokens).status_code == 204

    stored = users.get_by_id(user_id)
    assert stored.deactivated_at is not None
    assert stored.telegram_user_id is None and stored.telegram_linked_at is None
    assert users.get_by_telegram_user_id(TELEGRAM_USER_ID) is None
    assert client.get("/users/me", headers=_headers(other)).status_code == 401
    assert get_user_device_directory().get_fcm_tokens(user_id) == []
    assert reminder_sync.cancelled_users == [user_id]


def test_no_reminder_of_an_inactive_account_can_be_notified(clean_db, reminder_sync):
    """RF-USR-09: ningún recordatorio de esa cuenta genera notificaciones. Usuario cancela los
    pendientes y el puerto que usa el envío informa la cuenta como inactiva y sin dispositivos."""
    tokens = _tokens(_register())
    client.put("/users/me/fcm-token", json={"fcm_token": "token-b"}, headers=_headers(tokens))
    user_id = _user_id(tokens)

    _deactivate(tokens)

    directory = get_user_device_directory()
    assert reminder_sync.cancelled_users == [user_id]
    assert directory.is_active(user_id) is False
    assert directory.get_fcm_tokens(user_id) == []


def test_inactive_account_is_not_accessible_through_identity_service(clean_db):
    """RF-USR-09: los datos de una cuenta inactiva no son accesibles por ningún canal, aunque
    su sesión siguiera abierta."""
    tokens = _tokens(_register())
    user_id = _user_id(tokens)
    _move_deactivation_back(clean_db, user_id, days=0)

    with pytest.raises(ValueError):
        get_identity_service().authenticate(tokens["access_token"])
    assert client.get("/users/me", headers=_headers(tokens)).status_code == 401


def test_login_within_30_days_reactivates_the_account(clean_db, reminder_sync):
    """RF-USR-09 y RF-USR-02: iniciar sesión dentro de los 30 días reactiva la cuenta.
    Lo cancelado no se restaura: Telegram sigue desvinculado."""
    email = _register()
    tokens = _tokens(email)
    user_id = _user_id(tokens)
    _deactivate(tokens)
    _move_deactivation_back(clean_db, user_id, days=29)

    login = _login(email)

    assert login.status_code == 200
    profile = client.get("/users/me", headers=_headers(login.json())).json()
    assert profile["status"] == "active"
    assert profile["telegram_linked"] is False
    assert SqlAlchemyUserRepository(clean_db).get_by_id(user_id).deactivated_at is None


def test_login_after_30_days_returns_403(clean_db):
    """RF-USR-09 y RF-USR-02: después de 30 días → 403 y la cuenta sigue inactiva."""
    email = _register()
    tokens = _tokens(email)
    user_id = _user_id(tokens)
    _deactivate(tokens)
    _move_deactivation_back(clean_db, user_id, days=31)

    login = _login(email)

    assert login.status_code == 403
    assert SqlAlchemyUserRepository(clean_db).get_by_id(user_id).deactivated_at is not None


def test_wrong_password_on_an_inactive_account_keeps_the_generic_401():
    """RF-USR-02: con una contraseña incorrecta la respuesta no revela que la cuenta está inactiva."""
    email = _register()
    _deactivate(_tokens(email))

    login = client.post("/users/login", json={"email": email, "password": "clave-incorrecta"})

    assert login.status_code == 401


def test_email_stays_reserved_after_deactivating():
    """RF-USR-09: el correo sigue reservado."""
    email = _register()
    _deactivate(_tokens(email))

    again = client.post(
        "/users", json={"full_name": "Otra", "email": email, "password": TEST_PASSWORD, **CONSENT}
    )

    assert again.status_code == 409


class _FixedClock:
    def __init__(self) -> None:
        self.now = now_bogota()

    def __call__(self):
        return self.now


def _in_memory_account():
    hasher = Pbkdf2PasswordHasher()
    users, sessions = InMemoryUserRepository(), InMemorySessionRepository()
    user = Usuario.create("Ana", Email("ana@example.com"), hasher.hash(TEST_PASSWORD))
    users.add(user)
    return hasher, users, sessions, user


def test_reactivation_window_ends_exactly_at_30_days():
    """RF-USR-09: el plazo es `now - deactivated_at <= 30 días`; un segundo después → inactiva."""
    hasher, users, sessions, user = _in_memory_account()
    clock = _FixedClock()
    login = LoginUserUseCase(
        users, hasher, JwtTokenService(), InMemoryFailedLoginAttemptRepository(), sessions, clock
    )

    user.deactivated_at = clock.now - timedelta(days=30, seconds=1)
    with pytest.raises(InactiveUserError):
        login.execute("ana@example.com", TEST_PASSWORD)

    user.deactivated_at = clock.now - timedelta(days=30)
    login.execute("ana@example.com", TEST_PASSWORD)
    assert users.get_by_id(user.id).deactivated_at is None


def test_wrong_password_changes_nothing_in_memory():
    """RF-USR-09: sin la contraseña correcta no se desactiva ni se cancela nada."""
    hasher, users, sessions, user = _in_memory_account()
    recorder = RecordingReminderSync()
    use_case = DeactivateAccountUseCase(users, hasher, sessions, recorder)

    with pytest.raises(IncorrectPasswordError):
        use_case.execute(user.id, "clave-incorrecta")

    assert user.deactivated_at is None
    assert recorder.cancelled_users == []
