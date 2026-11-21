"""Puerto de entrada de Usuario para los dispositivos y el estado de la cuenta.

Reminders lo usa al enviar notificaciones (RF-NOT-01, 02 y 04): obtiene los
tokens FCM del usuario, informa los que FCM reporta como inválidos y comprueba
que la cuenta siga activa. Ningún otro módulo lee la tabla `sessions`.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class UserDeviceDirectory(Protocol):
    """Contrato público de Usuario para los dispositivos registrados."""

    def get_fcm_tokens(self, user_id: UUID) -> list[str]:
        """Tokens FCM de las sesiones activas del usuario. Lista vacía si no hay."""
        ...

    def invalidate_fcm_token(self, fcm_token: str) -> None:
        """Pone en `NULL` un token que FCM reportó como inválido."""
        ...

    def is_active(self, user_id: UUID) -> bool:
        """Indica si la cuenta existe y está activa (RF-USR-09)."""
        ...


_service: UserDeviceDirectory | None = None


def configure_user_device_directory(service: UserDeviceDirectory) -> None:
    global _service
    _service = service


def get_user_device_directory() -> UserDeviceDirectory:
    if _service is None:
        raise RuntimeError("El directorio de dispositivos no ha sido configurado.")
    return _service
