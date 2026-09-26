from datetime import datetime

from app.modules.reminders.application.ports.inbound.reminder_ports import (
    ScheduleNotificationPort,
)
from app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from app.modules.reminders.domain.entities import Notification


class ScheduleNotificationUseCase(ScheduleNotificationPort):
    """Creates the Notification record associated with a Reminder.

    Does not send it (that's SendNotificationUseCase's job).
    `now` can be injected for deterministic tests; if omitted, the
    current system time is used.
    """

    def __init__(self, repository: ReminderRepository):
        self._repository = repository

    def execute(self, reminder_id: int, now: datetime | None = None) -> Notification:
        reminder = self._repository.get_by_id(reminder_id)
        if reminder is None:
            raise ValueError("Recordatorio no encontrado")

        return Notification(
            reminder_id=reminder.id,
            message=reminder.message,
            read_status=False,
            date_send=now or datetime.now(),
        )
