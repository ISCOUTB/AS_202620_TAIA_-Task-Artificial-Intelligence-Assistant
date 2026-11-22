"""Puerto para las solicitudes de "olvidé mi contraseña" (RF-USR-08, RNF-03)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class PasswordResetRequestRepository(ABC):
    @abstractmethod
    def add(self, email: str, requested_at: datetime) -> None:
        """Registra una solicitud con el correo normalizado, exista o no la cuenta."""

    @abstractmethod
    def count_since(self, email: str, since: datetime) -> int:
        """Cuenta las solicitudes del correo desde `since`."""
