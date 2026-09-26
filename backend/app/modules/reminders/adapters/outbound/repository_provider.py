from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.adapters.outbound.sqlalchemy_reminder_repository import SQLAlchemyReminderRepository
from app.shared.adapters.outbound.database import get_session_factory

_repository: ReminderRepository = SQLAlchemyReminderRepository(get_session_factory())
def get_reminder_repository() -> ReminderRepository:
    return _repository
