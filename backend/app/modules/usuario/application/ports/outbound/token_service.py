"""Puerto para emisión y validación de tokens de autenticación."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.modules.usuario.domain.entities.usuario import Usuario


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user: Usuario) -> str:
        """Genera un token de acceso para el usuario."""

    @abstractmethod
    def verify_access_token(self, token: str) -> str:
        """Valida el token y devuelve el identificador del usuario (sub)."""
