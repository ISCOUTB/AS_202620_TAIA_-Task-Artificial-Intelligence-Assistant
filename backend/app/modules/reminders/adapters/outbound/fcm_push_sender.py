"""Envío push con Firebase Cloud Messaging (RF-NOT-02, D-10).

La cuenta de servicio llega como contenido JSON en `FIREBASE_CREDENTIALS_JSON`,
sin valor por defecto (RNF-02). Si falta o no es válida, el envío push queda
desactivado y la API arranca igual (RNF-09): las notificaciones se guardan en la
bandeja como en RF-NOT-04.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from functools import partial

import firebase_admin
from firebase_admin import credentials, exceptions, messaging

from app.modules.reminders.application.ports.outbound.push_sender import (
    InvalidPushTokenError,
    PushDeliveryError,
    PushSender,
)

logger = logging.getLogger("taia.reminders")

CREDENTIALS_ENV = "FIREBASE_CREDENTIALS_JSON"
APP_NAME = "taia-fcm"
TITLE = "TAIA"

# Errores con los que FCM indica que el token ya no sirve y hay que borrarlo.
_INVALID_TOKEN_ERRORS = (
    messaging.UnregisteredError,
    messaging.SenderIdMismatchError,
    exceptions.InvalidArgumentError,
)


class FcmPushSender(PushSender):
    def __init__(self, send: Callable[[messaging.Message], str]) -> None:
        """`send` es `firebase_admin.messaging.send` con la app de TAIA; las pruebas pasan un doble."""

        self._send = send

    @classmethod
    def from_env(cls) -> FcmPushSender | None:
        raw = os.getenv(CREDENTIALS_ENV)
        if not raw:
            logger.warning("fcm_disabled", extra={"fields": {"reason": f"{CREDENTIALS_ENV} no está configurada"}})
            return None
        try:
            certificate = credentials.Certificate(json.loads(raw))
        except ValueError:
            # json.JSONDecodeError también es un ValueError. No se registra el contenido.
            logger.warning("fcm_disabled", extra={"fields": {"reason": f"{CREDENTIALS_ENV} no es válida"}})
            return None
        app = firebase_admin.initialize_app(certificate, name=APP_NAME)
        return cls(partial(messaging.send, app=app))

    def send(self, token: str, message: str) -> None:
        payload = messaging.Message(token=token, notification=messaging.Notification(title=TITLE, body=message))
        try:
            self._send(payload)
        except _INVALID_TOKEN_ERRORS as error:
            raise InvalidPushTokenError() from error
        except exceptions.FirebaseError as error:
            raise PushDeliveryError() from error
