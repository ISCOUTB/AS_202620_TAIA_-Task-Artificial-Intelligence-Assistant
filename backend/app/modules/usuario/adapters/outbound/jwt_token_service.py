"""Adaptador JWT para autenticación."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

from backend.app.modules.usuario.application.ports.outbound.token_service import TokenService
from backend.app.modules.usuario.domain.entities.usuario import Usuario


class JwtTokenService(TokenService):
    """Genera y valida tokens JWT firmados para acceder a la API de TAIA."""

    algorithm = "HS256"
    expires_minutes = 30

    def __init__(self, secret: str | None = None) -> None:
        # En producción TAIA_JWT_SECRET debe configurarse como secreto del entorno.
        self._secret = secret or os.getenv(
            "TAIA_JWT_SECRET",
            "dev-only-change-me-please-set-a-real-secret",
        )

    def create_access_token(self, user: Usuario) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": str(user.email),
            "iat": now,
            "exp": now + timedelta(minutes=self.expires_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self.algorithm)

    def verify_access_token(self, token: str) -> str:
        """Valida firma/expiración y devuelve el subject del token."""
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self.algorithm],
                options={"require": ["sub", "exp"]},
            )
        except InvalidTokenError as error:
            raise ValueError("Token de acceso inválido o expirado.") from error

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("Token de acceso inválido o expirado.")
        return subject
