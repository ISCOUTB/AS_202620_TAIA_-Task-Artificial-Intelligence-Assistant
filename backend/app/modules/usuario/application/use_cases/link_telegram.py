"""Casos de uso para vincular una cuenta Telegram existente."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from backend.app.modules.usuario.application.ports.outbound.telegram_link_repository import (
    TelegramLinkRepository,
    TelegramLinkToken,
)
from backend.app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from backend.app.modules.usuario.domain.entities.usuario import Usuario


class TelegramLinkTokenInvalidError(ValueError):
    """El token no existe, expiró o ya fue utilizado."""


class TelegramAlreadyLinkedError(ValueError):
    """La cuenta Telegram ya está vinculada a otro usuario."""


class UserAlreadyLinkedError(ValueError):
    """El usuario ya tiene una cuenta Telegram vinculada."""


class CreateTelegramLinkUseCase:
    """Crea un token de un solo uso para vincular Telegram."""

    token_ttl_minutes = 10

    def __init__(self, users: UserRepository, links: TelegramLinkRepository) -> None:
        self._users = users
        self._links = links

    def execute(self, user_id: uuid.UUID) -> TelegramLinkToken:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise ValueError("Usuario no encontrado.")
        if user.telegram_user_id is not None:
            raise UserAlreadyLinkedError("El usuario ya tiene una cuenta Telegram vinculada.")

        token = secrets.token_urlsafe(32)
        link = TelegramLinkToken(
            token=token,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=self.token_ttl_minutes),
        )
        self._links.save(link)
        return link


class ConfirmTelegramLinkUseCase:
    """Confirma la identidad recibida desde Telegram y completa la vinculación."""

    def __init__(self, users: UserRepository, links: TelegramLinkRepository) -> None:
        self._users = users
        self._links = links

    def execute(self, token: str, telegram_user_id: int) -> Usuario:
        if telegram_user_id <= 0:
            raise ValueError("El identificador de Telegram no es válido.")

        link = self._links.get(token)
        now = datetime.now(timezone.utc)
        if link is None or link.used or link.expires_at <= now:
            raise TelegramLinkTokenInvalidError("El token de vinculación es inválido o expiró.")

        # Un Telegram existente solo puede pertenecer a un usuario TAIA.
        for candidate in self._all_users():
            if candidate.telegram_user_id == telegram_user_id and candidate.id != link.user_id:
                raise TelegramAlreadyLinkedError("La cuenta Telegram ya está vinculada a otro usuario.")

        user = self._users.get_by_id(link.user_id)
        if user is None:
            raise TelegramLinkTokenInvalidError("El usuario de vinculación ya no existe.")
        if user.telegram_user_id is not None:
            raise UserAlreadyLinkedError("El usuario ya tiene una cuenta Telegram vinculada.")

        user.link_telegram(telegram_user_id)
        self._links.mark_used(token)
        return user

    def _all_users(self) -> list[Usuario]:
        return self._users.list_all()
