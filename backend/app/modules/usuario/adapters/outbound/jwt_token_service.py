"""Adaptador JWT para autenticación."""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

from app.modules.usuario.application.ports.outbound.token_service import AccessTokenClaims, TokenService
from app.modules.usuario.domain.entities.usuario import Usuario


class JwtTokenService(TokenService):
    """Genera y valida tokens JWT firmados para acceder a la API de TAIA."""

    algorithm = "HS256"
    expires_minutes = 30
    refresh_token_bytes = 32

    def __init__(self, secret: str | None = None) -> None:
        # RNF-02: sin secreto no hay valor por defecto y la API no arranca.
        self._secret = secret or os.getenv("TAIA_JWT_SECRET")
        if not self._secret:
            raise RuntimeError("La variable de entorno TAIA_JWT_SECRET no está configurada.")

    def create_access_token(self, user: Usuario, session_id: uuid.UUID) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "sid": str(session_id),
            "email": str(user.email),
            "iat": now,
            "exp": now + timedelta(minutes=self.expires_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self.algorithm)

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        """Valida firma/expiración y devuelve el usuario y la sesión del token."""
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self.algorithm],
                # T-08: sin `sid` no hay sesión que revocar, así que el token no vale.
                options={"require": ["sub", "sid", "exp"]},
            )
            session_id = uuid.UUID(str(payload["sid"]))
        except (InvalidTokenError, ValueError) as error:
            raise ValueError("Token de acceso inválido o expirado.") from error

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("Token de acceso inválido o expirado.")
        return AccessTokenClaims(user_id=subject, session_id=session_id)

    def create_refresh_token(self) -> str:
        # Opaco y aleatorio: no es un JWT, solo vale lo que diga la base (RF-USR-03).
        return secrets.token_urlsafe(self.refresh_token_bytes)
