from datetime import datetime, timezone
from uuid import UUID

from backend.app.modules.reminders.application.ports.inbound.reminder_ports import (
    EditReminderPort,
)
from backend.app.modules.reminders.application.ports.outbound.reminder_repository import (
    ReminderRepository,
)
from backend.app.modules.reminders.domain.entities import Reminder


class EditReminderUseCase(EditReminderPort):
    """Edits the message and/or scheduled date of an existing reminder."""

    def __init__(self, repository: ReminderRepository):
        self._repository = repository

    def execute(
        self,
        reminder_id: int,
        user_id: UUID,
        message: str | None = None,
        scheduled_at: datetime | None = None,
    ) -> Reminder:
        reminder = self._repository.get_by_id(reminder_id)
        if reminder is None or reminder.user_id != user_id:
            raise ValueError("Recordatorio no encontrado")

        if reminder.is_completed:
            raise ValueError("No se puede editar un recordatorio ya completado")

        if message is not None and not message.strip():
            raise ValueError("El mensaje no puede estar vacío")

        if scheduled_at is not None:
            candidate = scheduled_at if scheduled_at.tzinfo else scheduled_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if candidate <= now:
                raise ValueError("La fecha programada debe ser futura")

        updated = reminder.model_copy(
            update={
                "message": message.strip() if message is not None else reminder.message,
                "scheduled_at": scheduled_at if scheduled_at is not None else reminder.scheduled_at,
            }
        )
        return self._repository.update(updated)
