"""Envío del código de recuperación con la API HTTP de Resend (RF-USR-08, H-01).

La clave sale de `RESEND_API` y el remitente de `RESEND_FROM`, ambas sin valor por
defecto. Si falta alguna, `from_env` devuelve None y la solicitud responde 503.
"""

from __future__ import annotations

import os

import httpx

from app.modules.usuario.application.ports.outbound.password_reset_mailer import (
    PasswordResetMailError,
    PasswordResetMailer,
)

RESEND_EMAILS_URL = "https://api.resend.com/emails"
_TIMEOUT_SECONDS = 10.0

# Borrador pendiente de revisión del equipo (RESULTADOS.md del frente A, sección 7).
SUBJECT = "Tu código para restablecer la contraseña de TAIA"
BODY = (
    "Hola:\n\n"
    "Recibimos una solicitud para restablecer la contraseña de tu cuenta de TAIA.\n\n"
    "Tu código de verificación es: {code}\n\n"
    "Escríbelo en la aplicación junto con tu nueva contraseña. El código vence en 15 minutos "
    "y sirve una sola vez.\n\n"
    "Si no pediste este cambio, ignora este correo: tu contraseña no cambia.\n\n"
    "TAIA"
)


class ResendPasswordResetMailer(PasswordResetMailer):
    def __init__(self, api_key: str, sender: str, client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._sender = sender
        self._client = client

    @classmethod
    def from_env(cls) -> "ResendPasswordResetMailer | None":
        api_key = os.getenv("RESEND_API")
        sender = os.getenv("RESEND_FROM")
        if not api_key or not sender:
            return None
        return cls(api_key, sender)

    def send_code(self, email: str, code: str) -> None:
        if self._client is not None:
            self._post(self._client, email, code)
            return
        with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
            self._post(client, email, code)

    def _post(self, client: httpx.Client, email: str, code: str) -> None:
        try:
            response = client.post(
                RESEND_EMAILS_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "from": self._sender,
                    "to": [email],
                    "subject": SUBJECT,
                    "text": BODY.format(code=code),
                },
            )
        except httpx.HTTPError as error:
            # El mensaje no lleva la clave, el correo ni el código (RNF-05).
            raise PasswordResetMailError(type(error).__name__) from error
        if response.is_error:
            raise PasswordResetMailError(f"Resend respondió HTTP {response.status_code}")
