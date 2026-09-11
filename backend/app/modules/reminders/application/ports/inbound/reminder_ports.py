from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID
from backend.app.modules.reminders.domain.entities import Notification, Reminder

class CreateReminderPort(ABC):
    @abstractmethod
    def execute(self, user_id: UUID, message: str, scheduled_at: datetime, task_id: UUID) -> Reminder: raise NotImplementedError
class ListRemindersPort(ABC):
    @abstractmethod
    def execute(self, user_id: UUID) -> list[Reminder]: raise NotImplementedError
class GetReminderPort(ABC):
    @abstractmethod
    def execute(self, reminder_id: int, user_id: UUID) -> Reminder: raise NotImplementedError
class EditReminderPort(ABC):
    @abstractmethod
    def execute(self, reminder_id: int, user_id: UUID, message: str | None, scheduled_at: datetime | None) -> Reminder: raise NotImplementedError
class DeleteReminderPort(ABC):
    @abstractmethod
    def execute(self, reminder_id: int, user_id: UUID) -> None: raise NotImplementedError
class ScheduleNotificationPort(ABC):
    @abstractmethod
    def execute(self, reminder_id: int, now: datetime | None = None) -> Notification: raise NotImplementedError
class SendNotificationPort(ABC):
    @abstractmethod
    def execute(self, notification: Notification) -> bool: raise NotImplementedError
class MarkReminderCompletedPort(ABC):
    @abstractmethod
    def execute(self, reminder_id: int, user_id: UUID) -> Reminder: raise NotImplementedError
