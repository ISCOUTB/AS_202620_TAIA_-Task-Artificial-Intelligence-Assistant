"""Puerto para emisión y validación de tokens de autenticación."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.modules.usuario.domain.entities.usuario import Usuario


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: str
    session_id: uuid.UUID


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user: Usuario, session_id: uuid.UUID) -> str:
        """Genera un token de acceso ligado a la sesión (`sid`)."""

    @abstractmethod
    def verify_access_token(self, token: str) -> AccessTokenClaims:
        """Valida el token y devuelve el usuario (sub) y la sesión (sid)."""

    @abstractmethod
    def create_refresh_token(self) -> str:
        """Genera un token de renovación opaco."""
