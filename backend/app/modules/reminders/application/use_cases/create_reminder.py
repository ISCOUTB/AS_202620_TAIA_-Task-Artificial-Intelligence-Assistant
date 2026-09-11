from datetime import datetime
from uuid import UUID

from app.modules.reminders.application.ports.inbound.reminder_ports import (
    CreateReminderPort,
)
from app.modules.reminders.application.ports.outbound.academic_task_lookup import (
    AcademicTaskLookup,
)
from app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from app.modules.reminders.domain.entities import Reminder


class CreateReminderUseCase(CreateReminderPort):
    """Creates a new reminder linked to an academic task.

    `task_lookup` is optional on purpose: reminders must keep working
    even if Academic's read port isn't wired yet. When present, it is
    used to check that the referenced task actually exists and belongs
    to the same user, which is the only thing reminders needs to know
    about Academic (see ubiquitous language / context map doc).
    """

    def __init__(
        self,
        repository: ReminderRepository,
        task_lookup: AcademicTaskLookup | None = None,
    ):
        self._repository = repository
        self._task_lookup = task_lookup

    def execute(
        self, user_id: UUID, message: str, scheduled_at: datetime, task_id: int
    ) -> Reminder:
        if not message or not message.strip():
            raise ValueError("El mensaje no puede estar vacío")

        if scheduled_at <= datetime.now():
            raise ValueError("La fecha programada debe ser futura")

        if self._task_lookup is not None:
            task = self._task_lookup.get_summary(task_id)
            if task is None:
                raise ValueError("La tarea académica referenciada no existe")
            if task.owner_user_id != user_id:
                raise ValueError("La tarea académica no pertenece a este usuario")

        reminder = Reminder(
            id=self._repository.next_id(),
            user_id=user_id,
            message=message.strip(),
            scheduled_at=scheduled_at,
            task_id=task_id,
        )
        return self._repository.create(reminder)
