"""Puerto para tokens temporales de vinculación con Telegram."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class TelegramLinkToken:
    token: str
    user_id: uuid.UUID
    expires_at: datetime
    used: bool = False


class TelegramLinkRepository(ABC):
    @abstractmethod
    def save(self, link: TelegramLinkToken) -> None:
        """Guarda un token de vinculación."""

    @abstractmethod
    def get(self, token: str) -> TelegramLinkToken | None:
        """Obtiene un token de vinculación."""

    @abstractmethod
    def mark_used(self, token: str) -> None:
        """Marca un token como utilizado."""
