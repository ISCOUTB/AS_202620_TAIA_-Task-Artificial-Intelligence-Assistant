"""Puerto de salida para el envío push a un dispositivo (RF-NOT-02, D-10)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class InvalidPushTokenError(Exception):
    """El servicio push reporta el token como no registrado o inválido."""


class PushDeliveryError(Exception):
    """Fallo transitorio del servicio push: el envío se puede reintentar."""


class PushSender(ABC):
    @abstractmethod
    def send(self, token: str, message: str) -> None:
        """Envía `message` al dispositivo de `token`.

        Lanza `InvalidPushTokenError` o `PushDeliveryError`.
        """
        raise NotImplementedError
