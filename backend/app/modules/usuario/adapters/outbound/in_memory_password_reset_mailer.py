"""Doble en memoria del envío del código de recuperación: ninguna prueba envía correos (RF-USR-08)."""

from __future__ import annotations

from app.modules.usuario.application.ports.outbound.password_reset_mailer import PasswordResetMailer


class InMemoryPasswordResetMailer(PasswordResetMailer):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_code(self, email: str, code: str) -> None:
        self.sent.append((email, code))

    def last_code_for(self, email: str) -> str | None:
        return next((code for to, code in reversed(self.sent) if to == email), None)
