"""Regresiones de E-02 y E-05, con repositorios en memoria y sin red."""

import ast
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from app.modules.academic.adapters.outbound.in_memory_structure_repositories import InMemorySubjectRepository
from app.modules.academic.adapters.outbound.in_memory_task_repository import InMemoryTaskRepository
from app.modules.academic.application.services.task_management import AcademicTaskManagementService
from app.modules.academic.domain.entities.subject import Subject
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.application.dto import NewTask, TaskFilters
from app.shared.clock import now_bogota

ROOT = Path(__file__).resolve().parents[2]


def test_structure_dependencies_are_injected(monkeypatch):
    from app.modules.academic.adapters.inbound import structure_api as api
    services = [object(), object(), object()]
    for name in ("_subjects", "_schedule", "_period"):
        monkeypatch.setattr(api, name, None)
    with pytest.raises(RuntimeError):
        api.get_subjects_use_case()
    api.configure_structure_use_cases(*services)
    assert [api.get_subjects_use_case(), api.get_schedule_use_case(),
            api.get_period_use_case()] == services


def test_reminder_dependencies_are_injected(monkeypatch):
    from app.modules.reminders.adapters.inbound import http_controller as api
    monkeypatch.setattr(api, "_use_cases", None)
    with pytest.raises(RuntimeError):
        api.get_create_use_case()
    services = api.ReminderUseCases(*(object() for _ in range(8)))
    api.configure_reminder_use_cases(services)
    for name in services.__dataclass_fields__:
        assert getattr(api, f"get_{name}_use_case")() is getattr(services, name)


@pytest.mark.parametrize("name", [
    "academic/adapters/inbound/structure_api.py",
    "reminders/adapters/inbound/http_controller.py",
])
def test_http_controllers_do_not_compose_outbound_dependencies(name):
    tree = ast.parse((ROOT / "backend/app/modules" / name).read_text(encoding="utf-8"))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
    assert not any(".adapters.outbound." in module for module in imports)


def test_ai_only_imports_academic_public_inbound_contract():
    path = ROOT / "backend/app/modules/ai/adapters/outbound/academic_gateway.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
    assert all(module.startswith("app.modules.academic.application.ports.inbound.")
               for module in imports if module.startswith("app.modules.academic."))


@pytest.mark.parametrize("status,expected", [
    ("done", ["Terminada"]), ("COMPLETED", ["Terminada"]),
    ("pending", ["Pendiente"]), ("overdue", []),
    ("unknown", ["Pendiente", "Terminada"]),
])
def test_academic_owns_status_translation_and_enforces_ownership(status, expected):
    owner, other = uuid.uuid4(), uuid.uuid4()
    subjects = InMemorySubjectRepository()
    subject = Subject.create(owner, "Matemáticas")
    subjects.add(subject)
    service = AcademicTaskManagementService(InMemoryTaskRepository(subjects), subjects)
    gateway = AcademicGatewayAdapter(service)
    for title in ["Pendiente", "Terminada"]:
        task = gateway.create_task(str(owner), NewTask(
            title=title, subject="Matemáticas", due_at=now_bogota() + timedelta(days=3)))
        if title == "Terminada":
            service.complete_task(uuid.UUID(task.id), owner)
    filters = TaskFilters(status=status)
    assert sorted(t.title for t in gateway.list_tasks(str(owner), filters)) == expected
    assert gateway.list_tasks(str(other), filters) == []
