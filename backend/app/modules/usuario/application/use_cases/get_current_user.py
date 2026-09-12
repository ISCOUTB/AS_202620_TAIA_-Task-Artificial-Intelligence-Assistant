"""Caso de uso para recuperar el usuario autenticado."""

from __future__ import annotations

import uuid

from backend.app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from backend.app.modules.usuario.domain.entities.usuario import Usuario


class AuthenticatedUserNotFoundError(ValueError):
    """El usuario indicado por el token ya no existe."""


class GetCurrentUserUseCase:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, user_id: str) -> Usuario:
        try:
            parsed_id = uuid.UUID(user_id)
        except ValueError as error:
            raise AuthenticatedUserNotFoundError("Usuario autenticado no encontrado.") from error

        user = self._repository.get_by_id(parsed_id)
        if user is None:
            raise AuthenticatedUserNotFoundError("Usuario autenticado no encontrado.")
        return user
