from datetime import date
import uuid

import pytest

from backend.app.modules.academic.adapters.outbound.in_memory_task_repository import (
    InMemoryTaskRepository,
)
from backend.app.modules.academic.application.use_cases.register_task import RegisterTaskUseCase
from backend.app.modules.academic.application.use_cases.update_task import (
    TaskNotFoundError,
    UpdateTaskUseCase,
)


def test_update_task_changes_editable_fields():
    repository = InMemoryTaskRepository()
    user_id = uuid.uuid4()
    task = RegisterTaskUseCase(repository).execute(
        user_id=user_id,
        title="Tarea original",
        due_date=date(2026, 9, 10),
        subject="Arquitectura",
    )

    updated = UpdateTaskUseCase(repository).execute(
        task_id=task.id,
        user_id=user_id,
        title="Tarea actualizada",
        due_date=date(2026, 9, 12),
        subject="IA",
        description="Nueva descripción",
    )

    assert updated.title == "Tarea actualizada"
    assert updated.due_date == date(2026, 9, 12)
    assert updated.subject == "IA"
    assert updated.description == "Nueva descripción"


def test_update_task_rejects_other_user():
    repository = InMemoryTaskRepository()
    owner = uuid.uuid4()
    other = uuid.uuid4()
    task = RegisterTaskUseCase(repository).execute(
        user_id=owner,
        title="Privada",
        due_date=date(2026, 9, 10),
    )

    with pytest.raises(TaskNotFoundError):
        UpdateTaskUseCase(repository).execute(
            task_id=task.id,
            user_id=other,
            title="No autorizada",
        )
