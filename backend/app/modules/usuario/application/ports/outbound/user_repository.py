"""Puerto de persistencia del módulo Usuario."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: Usuario) -> None:
        """Persiste un usuario nuevo."""

    @abstractmethod
    def save(self, user: Usuario) -> None:
        """Persiste los cambios de un usuario existente."""

    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> Usuario | None:
        """Obtiene un usuario por su identificador."""

    @abstractmethod
    def get_by_email(self, email: Email) -> Usuario | None:
        """Obtiene un usuario por correo."""

    @abstractmethod
    def get_by_telegram_user_id(self, telegram_user_id: int) -> Usuario | None:
        """Obtiene el usuario vinculado a una cuenta de Telegram."""
