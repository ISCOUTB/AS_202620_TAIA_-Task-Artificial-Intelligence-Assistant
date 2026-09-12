from backend.app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from backend.app.modules.reminders.adapters.outbound.in_memory_reminder_repository import InMemoryReminderRepository
_repository: ReminderRepository = InMemoryReminderRepository()
def get_reminder_repository() -> ReminderRepository:
    return _repository
