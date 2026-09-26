from datetime import datetime
from uuid import UUID
from app.modules.reminders.application.ports.inbound.reminder_ports import CreateReminderPort
from app.modules.reminders.application.ports.outbound.academic_task_lookup import AcademicTaskLookup
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.domain.entities import Reminder
from app.shared.clock import Clock, as_bogota, now_bogota

class CreateReminderUseCase(CreateReminderPort):
    def __init__(self, repository: ReminderRepository, task_lookup: AcademicTaskLookup | None = None, now_provider: Clock | None = None):
        self._repository = repository
        self._task_lookup = task_lookup
        self._now_provider = now_provider or now_bogota

    def execute(self, user_id: UUID, message: str, scheduled_at: datetime, task_id: UUID) -> Reminder:
        if not message or not message.strip():
            raise ValueError('El mensaje no puede estar vacío')
        now = self._now_provider()
        scheduled = as_bogota(scheduled_at)
        if scheduled <= now:
            raise ValueError('La fecha programada debe ser futura')
        if self._task_lookup is not None:
            task = self._task_lookup.get_summary(task_id, user_id)
            if task is None:
                raise ValueError('La tarea académica referenciada no existe o no pertenece a este usuario')
        return self._repository.create(Reminder(id=self._repository.next_id(), user_id=user_id, message=message.strip(), scheduled_at=scheduled, task_id=task_id))
