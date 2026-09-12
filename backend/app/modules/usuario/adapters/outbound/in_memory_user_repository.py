"""Adaptador temporal en memoria para Usuario."""

from __future__ import annotations

import uuid

from backend.app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from backend.app.modules.usuario.domain.entities.usuario import Usuario
from backend.app.modules.usuario.domain.value_objects.email import Email


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[uuid.UUID, Usuario] = {}

    def add(self, user: Usuario) -> None:
        self._users[user.id] = user

    def get_by_id(self, user_id: uuid.UUID) -> Usuario | None:
        return self._users.get(user_id)

    def get_by_email(self, email: Email) -> Usuario | None:
        return next((user for user in self._users.values() if user.email == email), None)

    def list_all(self) -> list[Usuario]:
        return list(self._users.values())
