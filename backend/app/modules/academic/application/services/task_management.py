"""Servicio de aplicación para operaciones de tareas académicas."""

from uuid import UUID
from datetime import date

from backend.app.modules.academic.application.ports.inbound.task_management import (
    AcademicTaskData,
    AcademicTaskManagement,
)
from backend.app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from backend.app.modules.academic.application.use_cases.complete_task import CompleteTaskUseCase
from backend.app.modules.academic.application.use_cases.list_tasks import ListTasksUseCase
from backend.app.modules.academic.application.use_cases.register_task import RegisterTaskUseCase
from backend.app.modules.academic.application.use_cases.update_task import UpdateTaskUseCase


class AcademicTaskManagementService(AcademicTaskManagement):
    """Fachada de aplicación que mantiene el repositorio dentro de Academic."""

    def __init__(self, repository: TaskRepository) -> None:
        self._complete = CompleteTaskUseCase(repository)
        self._register = RegisterTaskUseCase(repository)
        self._list = ListTasksUseCase(repository)
        self._update = UpdateTaskUseCase(repository)

    def create_task(
        self,
        user_id: UUID,
        title: str,
        due_date: date,
        subject: str | None = None,
        description: str | None = None,
    ) -> AcademicTaskData:
        return _to_data(
            self._register.execute(
                user_id=user_id,
                title=title,
                due_date=due_date,
                subject=subject,
                description=description,
            )
        )

    def list_tasks(self, user_id: UUID) -> list[AcademicTaskData]:
        return [_to_data(task) for task in self._list.execute(user_id)]

    def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        title: str | None = None,
        due_date: date | None = None,
        subject: str | None = None,
        description: str | None = None,
    ) -> AcademicTaskData:
        return _to_data(
            self._update.execute(
                task_id=task_id,
                user_id=user_id,
                title=title,
                due_date=due_date,
                subject=subject,
                description=description,
            )
        )

    def complete_task(self, task_id: UUID, user_id: UUID) -> AcademicTaskData:
        return _to_data(self._complete.execute(task_id=task_id, user_id=user_id))


def _to_data(task) -> AcademicTaskData:
    return AcademicTaskData(
        task_id=task.id,
        owner_user_id=task.user_id,
        title=task.title,
        due_date=task.due_date,
        subject=task.subject,
        description=task.description,
        status=task.status.value,
    )
