"""Servicio de aplicación para operaciones de identidad."""

from __future__ import annotations

import uuid

from backend.app.modules.usuario.application.ports.inbound.identity import IdentityService
from backend.app.modules.usuario.application.ports.outbound.token_service import TokenService
from backend.app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from backend.app.modules.usuario.application.use_cases.get_current_user import GetCurrentUserUseCase


class IdentityServiceImpl(IdentityService):
    """Implementación de identidad independiente de FastAPI."""

    def __init__(self, repository: UserRepository, token_service: TokenService) -> None:
        self._repository = repository
        self._token_service = token_service

    def authenticate(self, access_token: str) -> uuid.UUID:
        user_id = self._token_service.verify_access_token(access_token)
        return GetCurrentUserUseCase(self._repository).execute(user_id).id

    def get_telegram_user_id(self, user_id: uuid.UUID) -> int | None:
        user = self._repository.get_by_id(user_id)
        return user.telegram_user_id if user is not None else None
