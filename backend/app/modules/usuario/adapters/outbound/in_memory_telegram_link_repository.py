"""Adaptador temporal en memoria para tokens de vinculación Telegram."""

from __future__ import annotations

from backend.app.modules.usuario.application.ports.outbound.telegram_link_repository import (
    TelegramLinkRepository,
    TelegramLinkToken,
)


class InMemoryTelegramLinkRepository(TelegramLinkRepository):
    def __init__(self) -> None:
        self._tokens: dict[str, TelegramLinkToken] = {}

    def save(self, link: TelegramLinkToken) -> None:
        self._tokens[link.token] = link

    def get(self, token: str) -> TelegramLinkToken | None:
        return self._tokens.get(token)

    def mark_used(self, token: str) -> None:
        link = self._tokens.get(token)
        if link is not None:
            link.used = True
