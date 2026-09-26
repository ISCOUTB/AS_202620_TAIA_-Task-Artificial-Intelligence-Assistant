"""Contrato de identidad que Usuario expone a otros contextos."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod


class IdentityService(ABC):
    """Puerto de entrada para resolver identidad sin depender del adaptador HTTP."""

    @abstractmethod
    def authenticate(self, access_token: str) -> uuid.UUID:
        """Valida un token y devuelve el identificador del usuario."""

    @abstractmethod
    def get_telegram_user_id(self, user_id: uuid.UUID) -> int | None:
        """Obtiene el identificador de Telegram vinculado al usuario."""


_identity_service: IdentityService | None = None


def configure_identity_service(service: IdentityService) -> None:
    """Configura la implementación en el composition root de la aplicación."""
    global _identity_service
    _identity_service = service


def get_identity_service() -> IdentityService:
    """Devuelve la implementación configurada del puerto de identidad."""
    if _identity_service is None:
        raise RuntimeError("El servicio de identidad no ha sido configurado.")
    return _identity_service
