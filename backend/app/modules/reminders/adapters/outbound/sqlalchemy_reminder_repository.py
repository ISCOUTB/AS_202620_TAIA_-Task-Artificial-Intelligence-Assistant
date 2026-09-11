"""Outbound adapter: concrete implementation of ReminderRepository using
SQLAlchemy. This is the only class in the reminders module that knows
about the ORM/database.

Adjust the session/ORM model names to match your actual project setup.
"""

from uuid import UUID

from app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from app.modules.reminders.domain.entities import Reminder

# from app.modules.reminders.adapters.outbound.models import ReminderModel


class SQLAlchemyReminderRepository(ReminderRepository):
    def __init__(self, session):
        self._session = session

    def next_id(self) -> int:
        raise NotImplementedError("Definir estrategia de ID (autoincrement/sequence)")

    def create(self, reminder: Reminder) -> Reminder:
        raise NotImplementedError("Mapear Reminder -> ReminderModel y hacer commit")

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        raise NotImplementedError

    def list_by_user(self, user_id: UUID) -> list[Reminder]:
        raise NotImplementedError

    def update(self, reminder: Reminder) -> Reminder:
        raise NotImplementedError

    def delete(self, reminder_id: int) -> None:
        raise NotImplementedError
