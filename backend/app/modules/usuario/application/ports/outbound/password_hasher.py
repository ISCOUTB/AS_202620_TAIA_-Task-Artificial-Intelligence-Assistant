"""Puerto para proteger y verificar contraseñas."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        """Genera una representación protegida de la contraseña."""

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Comprueba una contraseña contra su representación protegida."""
