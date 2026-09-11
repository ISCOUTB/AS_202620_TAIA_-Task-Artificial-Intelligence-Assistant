from datetime import datetime, timezone, timedelta
import uuid

from backend.app.modules.academic.adapters.outbound.repository_provider import get_task_repository
from backend.app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from backend.app.modules.ai.application.dto import NewTask, TaskFilters

TZ = timezone(timedelta(hours=-5))


def test_ai_gateway_creates_and_reads_from_academic_repository():
    user_id = uuid.uuid4()
    gateway = AcademicGatewayAdapter()

    created = gateway.create_task(
        str(user_id),
        NewTask(
            title="Preparar parcial",
            due_at=datetime(2026, 9, 20, 20, 0, tzinfo=TZ),
            subject="Arquitectura",
        ),
    )

    found = gateway.list_tasks(str(user_id), TaskFilters())

    assert found == [created]
    assert found[0].title == "Preparar parcial"
    assert found[0].status == "pending"


def test_ai_gateway_keeps_users_isolated():
    gateway = AcademicGatewayAdapter()
    owner = uuid.uuid4()
    other = uuid.uuid4()

    gateway.create_task(
        str(owner),
        NewTask(
            title="Solo del dueño",
            due_at=datetime(2026, 9, 20, tzinfo=TZ),
        ),
    )

    assert gateway.list_tasks(str(other), TaskFilters()) == []
