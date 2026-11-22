"""RF-NOT-02 y RF-NOT-04 · Envío de los recordatorios cuya hora ya llegó (ADR-0012)."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable, Sequence
from datetime import datetime

from app.modules.reminders.application.ports.outbound.academic_task_lookup import AcademicTaskLookup
from app.modules.reminders.application.ports.outbound.push_sender import (
    InvalidPushTokenError,
    PushDeliveryError,
    PushSender,
)
from app.modules.reminders.application.ports.outbound.reminder_repository import (
    NotificationRepository,
    ReminderRepository,
)
from app.modules.reminders.domain.entities import Notification, Reminder, default_message
from app.modules.usuario.application.ports.inbound.user_devices import UserDeviceDirectory
from app.shared.clock import as_bogota

logger = logging.getLogger("taia.reminders")

# Un intento inicial y hasta 3 reintentos con espera creciente, en segundos (RF-NOT-02).
RETRY_DELAYS = (1.0, 2.0, 4.0)


class DispatchDueRemindersUseCase:
    """Notifica cada recordatorio `pending` vencido como máximo una vez.

    La idempotencia la da `ReminderRepository.claim` (UPDATE condicional del
    diccionario §7.1), no el planificador: dos ejecuciones seguidas o dos procesos
    a la vez generan una sola notificación.
    """

    def __init__(
        self,
        reminders: ReminderRepository,
        notifications: NotificationRepository,
        tasks: AcademicTaskLookup,
        devices: UserDeviceDirectory,
        push_sender: PushSender | None,
        sleep: Callable[[float], None] = time.sleep,
        retry_delays: Sequence[float] = RETRY_DELAYS,
    ) -> None:
        self._reminders = reminders
        self._notifications = notifications
        self._tasks = tasks
        self._devices = devices
        self._push_sender = push_sender
        self._sleep = sleep
        self._retry_delays = tuple(retry_delays)

    def execute(self, now: datetime) -> int:
        """Procesa los vencidos a `now` (con zona, RT-03). Devuelve cuántos notificó."""

        now = as_bogota(now)
        notified = 0
        for reminder in self._reminders.list_due(now):
            try:
                if self._dispatch(reminder, now):
                    notified += 1
            except Exception as error:
                # Un recordatorio que falla no puede detener a los demás: antes, un
                # solo IntegrityError abortaba el lote en cada ejecución y ningún
                # usuario recibía notificaciones. Sin datos del usuario (RNF-05).
                logger.error(
                    "reminder_dispatch_item_failed",
                    extra={"fields": {"reminder_id": str(reminder.id), "error": type(error).__name__}},
                )
        return notified

    def _dispatch(self, reminder: Reminder, now: datetime) -> bool:
        active = self._devices.is_active(reminder.user_id)
        task = self._tasks.get(reminder.task_id, reminder.user_id) if active else None
        if task is None or task.completed:
            # Actividad completada o eliminada, o cuenta inactiva: no se notifica.
            self._reminders.cancel([reminder.id])
            return False
        notification = Notification(
            id=uuid.uuid4(),
            reminder_id=reminder.id,
            message=reminder.custom_message or default_message(task.title, task.subject_name, task.due_at),
            created_at=now,
        )
        if not self._reminders.claim(reminder.id, notification):
            return False
        self._push(notification, reminder, now)
        return True

    def _push(self, notification: Notification, reminder: Reminder, now: datetime) -> None:
        tokens = list(dict.fromkeys(self._devices.get_fcm_tokens(reminder.user_id)))
        if not tokens or self._push_sender is None:
            # RF-NOT-04: sin dispositivos (o sin FCM configurado) queda en la bandeja.
            return
        attempts, sent_at = 0, None
        for delay in (0.0, *self._retry_delays):
            if delay:
                self._sleep(delay)
            attempts += 1
            tokens, delivered = self._send_once(tokens, notification.message)
            if delivered and sent_at is None:
                sent_at = now
            if not tokens:
                break
        self._notifications.record_push(notification.id, attempts, sent_at)

    def _send_once(self, tokens: list[str], message: str) -> tuple[list[str], bool]:
        """Envía a cada token. Devuelve los que hay que reintentar y si alguno recibió."""

        retry, delivered = [], False
        for token in tokens:
            try:
                self._push_sender.send(token, message)
            except InvalidPushTokenError:
                self._devices.invalidate_fcm_token(token)
            except PushDeliveryError:
                retry.append(token)
            else:
                delivered = True
        return retry, delivered
