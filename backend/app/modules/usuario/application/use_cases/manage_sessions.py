"""Casos de uso de sesión: emitir, autenticar, renovar y cerrar (RF-USR-03, 04; T-08)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.modules.usuario.application.ports.outbound.session_repository import SessionRepository
from app.modules.usuario.application.ports.outbound.token_service import AccessTokenClaims, TokenService
from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.modules.usuario.domain.entities.usuario import Usuario, UserStatus
from app.shared.clock import Clock, now_bogota

# RF-USR-03: el token de renovación dura 30 días; el de acceso, 30 minutos.
REFRESH_TOKEN_LIFETIME = timedelta(days=30)


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class RevokedSessionError(ValueError):
    """El token de acceso pertenece a una sesión cerrada o revocada."""


class InvalidRefreshTokenError(ValueError):
    """El token de renovación no existe, expiró, ya se usó o su sesión está revocada."""


def start_session(
    user: Usuario, sessions: SessionRepository, token_service: TokenService, now: Clock = now_bogota
) -> TokenPair:
    """Abre una sesión nueva y emite su primer par de tokens."""
    session_id = uuid.uuid4()
    refresh_token = token_service.create_refresh_token()
    sessions.create(session_id, user.id, refresh_token, now() + REFRESH_TOKEN_LIFETIME)
    return TokenPair(token_service.create_access_token(user, session_id), refresh_token)


class AuthenticateAccessTokenUseCase:
    """Valida el JWT y que su sesión siga activa: así un token robado se puede revocar."""

    def __init__(self, token_service: TokenService, sessions: SessionRepository) -> None:
        self._token_service = token_service
        self._sessions = sessions

    def execute(self, access_token: str) -> AccessTokenClaims:
        claims = self._token_service.verify_access_token(access_token)
        if not self._sessions.is_active(claims.session_id):
            raise RevokedSessionError("La sesión fue cerrada o revocada.")
        return claims


class RefreshSessionUseCase:
    """Rota el token de renovación: cada uno sirve una sola vez."""

    def __init__(
        self,
        repository: UserRepository,
        sessions: SessionRepository,
        token_service: TokenService,
        now: Clock = now_bogota,
    ) -> None:
        self._repository = repository
        self._sessions = sessions
        self._token_service = token_service
        self._now = now

    def execute(self, refresh_token: str) -> TokenPair:
        now = self._now()
        record = self._sessions.get_refresh_token(refresh_token)
        if record is None:
            raise InvalidRefreshTokenError("Token de renovación inválido o expirado.")

        if record.used:
            # Un token ya rotado solo lo tiene quien lo robó (o el dueño tras el robo):
            # se cierran todas las sesiones del usuario.
            self._sessions.revoke_all(record.user_id, now)
            raise InvalidRefreshTokenError("Token de renovación inválido o expirado.")

        if record.session_revoked or record.expires_at <= now:
            raise InvalidRefreshTokenError("Token de renovación inválido o expirado.")

        user = self._repository.get_by_id(record.user_id)
        if user is None or user.status is not UserStatus.ACTIVE:
            self._sessions.revoke(record.session_id, now)
            raise InvalidRefreshTokenError("Token de renovación inválido o expirado.")

        new_refresh_token = self._token_service.create_refresh_token()
        rotated = self._sessions.rotate_refresh_token(
            refresh_token, new_refresh_token, now + REFRESH_TOKEN_LIFETIME, now
        )
        if not rotated:
            # Otra petición lo usó entre la lectura y la rotación: misma regla de reutilización.
            self._sessions.revoke_all(record.user_id, now)
            raise InvalidRefreshTokenError("Token de renovación inválido o expirado.")

        return TokenPair(
            self._token_service.create_access_token(user, record.session_id),
            new_refresh_token,
        )


class LogoutUseCase:
    """Cierra la sesión del token: deja de valer el de acceso y el de renovación."""

    def __init__(self, sessions: SessionRepository, now: Clock = now_bogota) -> None:
        self._sessions = sessions
        self._now = now

    def execute(self, session_id: uuid.UUID) -> None:
        self._sessions.revoke(session_id, self._now())
