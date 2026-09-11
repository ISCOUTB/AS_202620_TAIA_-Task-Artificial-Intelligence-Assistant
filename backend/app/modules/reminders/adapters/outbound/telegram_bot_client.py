"""Small Telegram Bot API client with no external SDK dependency."""

from __future__ import annotations

import json
import os
from urllib import error, request


class TelegramBotApiClient:
    def __init__(self, token: str | None = None, timeout: float = 5.0) -> None:
        self._token = token or os.getenv("TAIA_TELEGRAM_BOT_TOKEN")
        self._timeout = timeout

    def send_message(self, *, chat_id: int, text: str) -> None:
        if not self._token:
            raise RuntimeError("TAIA_TELEGRAM_BOT_TOKEN no está configurado.")

        payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        endpoint = f"https://api.telegram.org/bot{self._token}/sendMessage"
        http_request = request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self._timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("No fue posible contactar la API de Telegram.") from exc

        if not body.get("ok"):
            description = body.get("description", "Telegram rechazó el mensaje.")
            raise RuntimeError(description)
