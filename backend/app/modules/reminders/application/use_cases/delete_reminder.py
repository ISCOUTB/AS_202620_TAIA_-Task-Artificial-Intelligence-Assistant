"""RF-REC-05 · Eliminar un recordatorio que no generó notificación."""

from __future__ import annotations

from uuid import UUID

from app.modules.reminders.application.errors import ReminderStateError
from app.modules.reminders.application.ports.inbound.reminder_ports import DeleteReminderPort
from app.modules.reminders.application.ports.outbound.reminder_repository import ReminderRepository
from app.modules.reminders.application.use_cases.get_reminder import get_owned


class DeleteReminderUseCase(DeleteReminderPort):
    """Solo `pending` o `cancelled`: un `sent` se conserva para la bandeja."""

    def __init__(self, repository: ReminderRepository) -> None:
        self._repository = repository

    def execute(self, reminder_id: UUID, user_id: UUID) -> None:
        get_owned(self._repository, reminder_id, user_id)
        if not self._repository.delete_unsent(reminder_id):
            raise ReminderStateError(
                "Un recordatorio enviado no se puede eliminar: conserva su notificación."
            )
