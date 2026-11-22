"""Puerto de salida para enviar el código de recuperación por correo (RF-USR-08)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordResetMailError(Exception):
    """El proveedor de correo no aceptó el mensaje."""


class PasswordResetMailer(ABC):
    @abstractmethod
    def send_code(self, email: str, code: str) -> None:
        """Envía el código al correo. Lanza `PasswordResetMailError` si el envío falla."""
