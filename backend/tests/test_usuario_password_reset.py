"""Recuperar la contraseña con un código de verificación (RF-USR-08, RNF-03)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.modules.usuario.adapters.inbound import api as usuario_api
from app.modules.usuario.adapters.outbound.in_memory_password_reset_mailer import InMemoryPasswordResetMailer
from app.modules.usuario.adapters.outbound.in_memory_password_reset_repositories import (
    InMemoryPasswordResetCodeRepository,
    InMemoryPasswordResetRequestRepository,
)
from app.modules.usuario.adapters.outbound.in_memory_session_repository import InMemorySessionRepository
from app.modules.usuario.adapters.outbound.in_memory_user_repository import InMemoryUserRepository
from app.modules.usuario.adapters.outbound.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.modules.usuario.application.ports.outbound.password_reset_mailer import (
    PasswordResetMailError,
    PasswordResetMailer,
)
from app.modules.usuario.application.use_cases.reset_password import (
    InvalidResetCodeError,
    RequestPasswordResetUseCase,
    ResetPasswordUseCase,
    generate_code,
)
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import now_bogota
from tests.helpers import CONSENT, TEST_PASSWORD

client = TestClient(app)
REQUEST_PATH = "/users/password-reset"
CONFIRM_PATH = "/users/password-reset/confirm"
NEW_PASSWORD = "clave-restablecida-2026"


@pytest.fixture(autouse=True)
def mailer(clean_db, monkeypatch) -> InMemoryPasswordResetMailer:
    """Tablas vacías y un doble del correo: ninguna prueba envía un correo real."""
    double = InMemoryPasswordResetMailer()
    monkeypatch.setattr(usuario_api, "_password_reset_mailer", double)
    return double


def _register() -> str:
    email = f"olvido-{uuid.uuid4().hex[:8]}@example.com"
    created = client.post(
        "/users", json={"full_name": "Ana", "email": email, "password": TEST_PASSWORD, **CONSENT}
    )
    assert created.status_code == 201, created.text
    return email


def _request(email: str):
    return client.post(REQUEST_PATH, json={"email": email})


def _confirm(email: str, code: str, new_password: str = NEW_PASSWORD):
    return client.post(CONFIRM_PATH, json={"email": email, "code": code, "new_password": new_password})


def _login(email: str, password: str):
    return client.post("/users/login", json={"email": email, "password": password})


def _wrong(code: str) -> str:
    return f"{(int(code) + 1) % 10**6:06d}"


def _stored_codes(clean_db) -> list:
    with clean_db() as db:
        return list(
            db.execute(
                text(
                    "SELECT token_hash, failed_attempts, created_at, expires_at, used_at "
                    "FROM password_reset_tokens ORDER BY created_at"
                )
            )
        )


def test_unknown_email_gets_the_same_202_and_nothing_is_sent(mailer):
    """RF-USR-08: correo inexistente → 202, igual que con un correo existente, y no se envía nada."""
    existing = _register()

    known = _request(existing)
    unknown = _request("nadie@example.com")

    assert known.status_code == unknown.status_code == 202
    assert known.content == unknown.content
    assert [to for to, _ in mailer.sent] == [existing]


def test_fourth_request_in_24_hours_gets_the_same_429_for_any_email(clean_db, mailer):
    """RF-USR-08 y RNF-03: la cuarta solicitud con el mismo correo en 24 horas → 429, exista o no
    la cuenta, con el mismo cuerpo, y no se envía nada."""
    existing = _register()
    for _ in range(3):
        assert _request(existing).status_code == 202
        assert _request("nadie@example.com").status_code == 202

    known = _request(existing)
    unknown = _request("nadie@example.com")

    assert known.status_code == unknown.status_code == 429
    assert known.json() == unknown.json()
    assert "por hoy" in known.json()["detail"]
    assert len(mailer.sent) == 3
    with clean_db() as db:
        rows = db.scalar(text("SELECT count(*) FROM password_reset_requests WHERE email = 'nadie@example.com'"))
    assert rows == 3


def test_requests_older_than_24_hours_do_not_count(clean_db):
    """RNF-03: el límite cuenta solo las solicitudes de las últimas 24 horas."""
    email = _register()
    for _ in range(3):
        _request(email)
    with clean_db.begin() as db:
        db.execute(text("UPDATE password_reset_requests SET requested_at = requested_at - interval '25 hours'"))

    assert _request(email).status_code == 202


def test_valid_code_resets_once_and_reusing_it_gets_400(mailer):
    """RF-USR-08: código válido → 200. Reutilizar ese código → 400."""
    email = _register()
    _request(email)
    code = mailer.last_code_for(email)

    first = _confirm(email, code)
    reused = _confirm(email, code, "otra-clave-segura-2026")

    assert first.status_code == 200
    assert reused.status_code == 400
    assert _login(email, TEST_PASSWORD).status_code == 401
    assert _login(email, NEW_PASSWORD).status_code == 200


def test_reset_revokes_every_session(mailer):
    """RF-USR-08: al restablecer la contraseña se revocan todas las sesiones."""
    email = _register()
    tokens = _login(email, TEST_PASSWORD).json()
    _request(email)

    _confirm(email, mailer.last_code_for(email))

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/users/me", headers=headers).status_code == 401
    assert client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_expired_code_gets_400(clean_db, mailer):
    """RF-USR-08: restablecer con un código expirado → 400."""
    email = _register()
    _request(email)
    with clean_db.begin() as db:
        db.execute(
            text(
                "UPDATE password_reset_tokens SET created_at = created_at - interval '16 minutes', "
                "expires_at = expires_at - interval '16 minutes'"
            )
        )

    assert _confirm(email, mailer.last_code_for(email)).status_code == 400
    assert _login(email, TEST_PASSWORD).status_code == 200


def test_after_five_wrong_attempts_the_right_code_also_gets_400(clean_db, mailer):
    """RF-USR-08: después de 5 intentos con un código incorrecto, el código correcto también → 400."""
    email = _register()
    _request(email)
    code = mailer.last_code_for(email)

    for _ in range(5):
        assert _confirm(email, _wrong(code)).status_code == 400

    assert _confirm(email, code).status_code == 400
    assert _stored_codes(clean_db)[0].failed_attempts == 5


def test_four_wrong_attempts_still_allow_the_right_code(mailer):
    """RF-USR-08: el código admite como máximo 5 intentos fallidos; con 4 sigue vigente."""
    email = _register()
    _request(email)
    code = mailer.last_code_for(email)
    for _ in range(4):
        _confirm(email, _wrong(code))

    assert _confirm(email, code).status_code == 200


def test_unknown_email_and_wrong_code_get_the_same_400(mailer):
    """RF-USR-08: un correo inexistente y un código incorrecto reciben el mismo 400."""
    email = _register()
    _request(email)
    code = mailer.last_code_for(email)

    unknown = _confirm("nadie@example.com", code)
    wrong = _confirm(email, _wrong(code))

    assert unknown.status_code == wrong.status_code == 400
    assert unknown.json() == wrong.json()


def test_a_new_request_invalidates_the_previous_code(clean_db, mailer):
    """RF-USR-08: solicitar uno nuevo invalida los anteriores (su `expires_at` pasa a la hora actual)."""
    email = _register()
    _request(email)
    _request(email)

    old, new = _stored_codes(clean_db)

    assert old.expires_at == new.created_at
    assert old.used_at is None
    assert _confirm(email, mailer.last_code_for(email)).status_code == 200


def test_code_is_six_digits_stored_as_hash_and_lasts_15_minutes(clean_db, mailer):
    """RF-USR-08: 6 dígitos, solo el hash en la base y expiración a los 15 minutos."""
    email = _register()
    _request(email)
    code = mailer.last_code_for(email)

    [stored] = _stored_codes(clean_db)

    assert len(code) == 6 and code.isdigit()
    assert stored.token_hash == hashlib.sha256(code.encode()).hexdigest()
    assert stored.expires_at - stored.created_at == timedelta(minutes=15)
    assert stored.failed_attempts == 0


def test_new_password_must_follow_the_registration_rules(clean_db, mailer):
    """RF-USR-08: la nueva contraseña cumple las reglas de RF-USR-01; si no, 422 y no se gasta el código."""
    email = _register()
    _request(email)
    code = mailer.last_code_for(email)

    weak = _confirm(email, code, "corta")

    assert weak.status_code == 422
    assert _stored_codes(clean_db)[0].failed_attempts == 0
    assert _confirm(email, code).status_code == 200


def test_missing_mail_configuration_gets_503_without_touching_anything(clean_db, monkeypatch, mailer):
    """RF-USR-08 (H-01): sin RESEND_API o RESEND_FROM la solicitud responde 503 y no revela nada."""
    monkeypatch.setattr(usuario_api, "_password_reset_mailer", None)
    existing = _register()

    known = _request(existing)
    unknown = _request("nadie@example.com")

    assert known.status_code == unknown.status_code == 503
    assert known.json() == unknown.json()
    with clean_db() as db:
        assert db.scalar(text("SELECT count(*) FROM password_reset_requests")) == 0


class _FailingMailer(PasswordResetMailer):
    def send_code(self, email: str, code: str) -> None:
        raise PasswordResetMailError("Resend respondió HTTP 500")


def _in_memory_user():
    hasher = Pbkdf2PasswordHasher()
    users = InMemoryUserRepository()
    user = Usuario.create("Ana", Email("ana@example.com"), hasher.hash(TEST_PASSWORD))
    users.add(user)
    return hasher, users, user


def test_mail_failure_keeps_the_same_response(monkeypatch, caplog):
    """RF-USR-08: si el envío falla, la respuesta sigue siendo 202 y el error queda en el log."""
    monkeypatch.setattr(usuario_api, "_password_reset_mailer", _FailingMailer())
    existing = _register()

    with caplog.at_level(logging.WARNING, logger="taia.usuario"):
        known = _request(existing)
    unknown = _request("nadie@example.com")

    assert known.status_code == unknown.status_code == 202
    assert known.content == unknown.content
    assert "usuario.password_reset_mail_failed" in caplog.text
    assert existing not in caplog.text


class _RecordingMailer(InMemoryPasswordResetMailer):
    def __init__(self, events: list) -> None:
        super().__init__()
        self._events = events

    def send_code(self, email: str, code: str) -> None:
        self._events.append("mail")
        super().send_code(email, code)


def _call_asgi(path: str, payload: dict, events: list) -> None:
    """Llama a la aplicación por ASGI y anota cuándo termina de enviarse la respuesta."""
    body = json.dumps(payload).encode()
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST",
        "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"", "root_path": "",
        "headers": [(b"host", b"testserver"), (b"content-type", b"application/json")],
        "client": ("testclient", 50000), "server": ("testserver", 80),
    }
    messages = [{"type": "http.request", "body": body, "more_body": False}]

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.start":
            events.append(message["status"])
        elif message["type"] == "http.response.body" and not message.get("more_body", False):
            events.append("response")

    asyncio.run(app(scope, receive, send))


def test_mail_is_sent_after_the_response(monkeypatch):
    """RF-USR-08: el correo se envía después de responder, para que el tiempo de respuesta no
    revele si la cuenta existe."""
    existing = _register()
    events: list = []
    monkeypatch.setattr(usuario_api, "_password_reset_mailer", _RecordingMailer(events))

    _call_asgi(REQUEST_PATH, {"email": existing}, events)

    assert events == [202, "response", "mail"]


def test_before_responding_nothing_depends_on_the_account():
    """RF-USR-08: antes de responder solo se registra la solicitud; el código se crea y se envía
    después, así que el trabajo previo a la respuesta es el mismo exista o no la cuenta."""
    _, users, _ = _in_memory_user()
    requests, codes = InMemoryPasswordResetRequestRepository(), InMemoryPasswordResetCodeRepository()
    mailer = InMemoryPasswordResetMailer()
    use_case = RequestPasswordResetUseCase(users, requests, codes, mailer)

    email = use_case.execute("Ana@Example.com")

    assert email == "ana@example.com"
    assert codes.codes == [] and mailer.sent == []

    use_case.deliver(email)

    assert len(codes.codes) == 1
    assert [to for to, _ in mailer.sent] == ["ana@example.com"]


class _Clock:
    def __init__(self) -> None:
        self.now = now_bogota()

    def __call__(self):
        return self.now


def test_code_expires_exactly_15_minutes_after_issue():
    """RF-USR-08: el código expira en 15 minutos."""
    hasher, users, _ = _in_memory_user()
    clock, mailer = _Clock(), InMemoryPasswordResetMailer()
    codes, sessions = InMemoryPasswordResetCodeRepository(), InMemorySessionRepository()
    request = RequestPasswordResetUseCase(users, InMemoryPasswordResetRequestRepository(), codes, mailer, clock)
    request.deliver(request.execute("ana@example.com"))
    reset = ResetPasswordUseCase(users, codes, hasher, sessions, clock)
    code = mailer.last_code_for("ana@example.com")

    clock.now += timedelta(minutes=15)
    with pytest.raises(InvalidResetCodeError):
        reset.execute("ana@example.com", code, NEW_PASSWORD)

    clock.now -= timedelta(seconds=1)
    reset.execute("ana@example.com", code, NEW_PASSWORD)


def test_deactivated_account_can_reset_its_password():
    """RF-USR-08: una cuenta desactivada también puede restablecer su contraseña. Reactivarla sigue
    dependiendo del inicio de sesión (RF-USR-09)."""
    hasher, users, user = _in_memory_user()
    clock, mailer = _Clock(), InMemoryPasswordResetMailer()
    user.deactivate(clock.now - timedelta(days=1))
    users.save(user)
    codes = InMemoryPasswordResetCodeRepository()
    request = RequestPasswordResetUseCase(users, InMemoryPasswordResetRequestRepository(), codes, mailer, clock)

    request.deliver(request.execute("ana@example.com"))
    ResetPasswordUseCase(users, codes, hasher, InMemorySessionRepository(), clock).execute(
        "ana@example.com", mailer.last_code_for("ana@example.com"), NEW_PASSWORD
    )

    stored = users.get_by_id(user.id)
    assert hasher.verify(NEW_PASSWORD, stored.password_hash)
    assert stored.deactivated_at is not None


def test_generated_codes_are_six_random_digits():
    """RF-USR-08: 6 dígitos aleatorios, con ceros a la izquierda si hace falta."""
    codes = {generate_code() for _ in range(200)}

    assert all(len(code) == 6 and code.isdigit() for code in codes)
    assert len(codes) > 150
