"""Outbound port for the actual delivery of notifications.

Implemented by a concrete adapter (Telegram, email, push, etc.).
The application layer only knows this contract.
"""

from abc import ABC, abstractmethod

from app.modules.reminders.domain.entities import Notification


class NotificationSender(ABC):
    """Outbound port of the reminders module for notification delivery."""

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """Sends the notification. Returns True if delivered successfully."""
        raise NotImplementedError
