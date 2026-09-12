"""Puerto de persistencia del módulo Usuario."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from backend.app.modules.usuario.domain.entities.usuario import Usuario
from backend.app.modules.usuario.domain.value_objects.email import Email


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: Usuario) -> None:
        """Persiste un usuario nuevo."""

    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> Usuario | None:
        """Obtiene un usuario por su identificador."""

    @abstractmethod
    def get_by_email(self, email: Email) -> Usuario | None:
        """Obtiene un usuario por correo."""

    @abstractmethod
    def list_all(self) -> list[Usuario]:
        """Obtiene los usuarios necesarios para validaciones de identidad."""
