"""Puerto para los intentos fallidos de inicio de sesión (RNF-03)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class FailedLoginAttemptRepository(ABC):
    @abstractmethod
    def add(self, email: str, attempted_at: datetime) -> None:
        """Registra un intento fallido con el correo normalizado."""

    @abstractmethod
    def count_since(self, email: str, since: datetime) -> int:
        """Cuenta los intentos fallidos del correo desde `since`."""
