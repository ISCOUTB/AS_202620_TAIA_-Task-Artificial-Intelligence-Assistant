"""Adaptador de Resend para el correo de recuperación (RF-USR-08, H-01). Sin correos reales:
todas las llamadas pasan por `httpx.MockTransport`."""

from __future__ import annotations

import json

import httpx
import pytest

from app.modules.usuario.adapters.outbound.resend_password_reset_mailer import (
    RESEND_EMAILS_URL,
    ResendPasswordResetMailer,
)
from app.modules.usuario.application.ports.outbound.password_reset_mailer import PasswordResetMailError

API_KEY = "re_clave_de_prueba"
SENDER = "TAIA <no-reply@example.com>"


def _mailer(handler) -> ResendPasswordResetMailer:
    return ResendPasswordResetMailer(API_KEY, SENDER, httpx.Client(transport=httpx.MockTransport(handler)))


def test_sends_the_code_with_the_resend_api():
    """RF-USR-08: el correo lleva el código; la clave va en el encabezado y el remitente sale de RESEND_FROM."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": "email-1"})

    _mailer(handler).send_code("ana@example.com", "042517")

    [request] = seen
    body = json.loads(request.content)
    assert str(request.url) == RESEND_EMAILS_URL
    assert request.method == "POST"
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert body["from"] == SENDER
    assert body["to"] == ["ana@example.com"]
    assert "042517" in body["text"]
    assert body["subject"]


def test_error_status_raises_a_mail_error():
    """RF-USR-08: una respuesta de error de Resend se informa como `PasswordResetMailError`."""
    mailer = _mailer(lambda request: httpx.Response(422, json={"message": "invalid"}))

    with pytest.raises(PasswordResetMailError):
        mailer.send_code("ana@example.com", "123456")


def test_transport_error_raises_a_mail_error_without_secrets():
    """RF-USR-08 y RNF-05: un fallo de red se informa sin la clave, el correo ni el código."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red", request=request)

    with pytest.raises(PasswordResetMailError) as raised:
        _mailer(handler).send_code("ana@example.com", "123456")

    message = str(raised.value)
    assert API_KEY not in message and "ana@example.com" not in message and "123456" not in message


@pytest.mark.parametrize("missing", ["RESEND_API", "RESEND_FROM"])
def test_from_env_needs_both_variables(monkeypatch, missing):
    """H-01: sin RESEND_API o sin RESEND_FROM no hay adaptador, y la solicitud responde 503."""
    monkeypatch.setenv("RESEND_API", API_KEY)
    monkeypatch.setenv("RESEND_FROM", SENDER)
    monkeypatch.delenv(missing)

    assert ResendPasswordResetMailer.from_env() is None


def test_from_env_builds_the_adapter_with_both_variables(monkeypatch):
    """H-01: con las dos variables, el adaptador queda configurado."""
    monkeypatch.setenv("RESEND_API", API_KEY)
    monkeypatch.setenv("RESEND_FROM", SENDER)

    assert isinstance(ResendPasswordResetMailer.from_env(), ResendPasswordResetMailer)
