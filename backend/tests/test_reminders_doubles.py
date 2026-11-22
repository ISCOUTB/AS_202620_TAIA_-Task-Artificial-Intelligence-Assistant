"""Dobles en memoria de los puertos que consume Reminders. No contiene pruebas."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timedelta

from app.modules.reminders.adapters.outbound.in_memory_reminder_repository import InMemoryReminderRepository
from app.modules.reminders.application.ports.outbound.academic_task_lookup import AcademicTaskLookup, TaskInfo
from app.modules.reminders.application.ports.outbound.push_sender import (
    InvalidPushTokenError,
    PushDeliveryError,
    PushSender,
)
from app.shared.clock import BOGOTA_TZ

NOW = datetime(2026, 10, 1, 10, 0, tzinfo=BOGOTA_TZ)


class FixedClock:
    def __init__(self, now: datetime = NOW) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class FakeTasks(AcademicTaskLookup):
    """Actividades por (task_id, user_id); una ausente equivale a eliminada o ajena."""

    def __init__(self) -> None:
        self.tasks: dict[tuple[uuid.UUID, uuid.UUID], TaskInfo] = {}

    def add(self, user_id: uuid.UUID, due_at: datetime = NOW + timedelta(days=7), title: str = "Informe",
            subject_name: str = "Cálculo", completed: bool = False) -> TaskInfo:
        task = TaskInfo(task_id=uuid.uuid4(), title=title, subject_name=subject_name, due_at=due_at,
                        completed=completed)
        self.tasks[(task.task_id, user_id)] = task
        return task

    def complete(self, user_id: uuid.UUID, task_id: uuid.UUID) -> None:
        self.tasks[(task_id, user_id)] = replace(self.tasks[(task_id, user_id)], completed=True)

    def delete(self, user_id: uuid.UUID, task_id: uuid.UUID) -> None:
        del self.tasks[(task_id, user_id)]

    def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskInfo | None:
        return self.tasks.get((task_id, user_id))


class FakeDevices:
    """Doble de `UserDeviceDirectory` (frente A)."""

    def __init__(self) -> None:
        self.tokens: dict[uuid.UUID, list[str]] = {}
        self.inactive: set[uuid.UUID] = set()
        self.invalidated: list[str] = []

    def get_fcm_tokens(self, user_id: uuid.UUID) -> list[str]:
        return list(self.tokens.get(user_id, []))

    def invalidate_fcm_token(self, fcm_token: str) -> None:
        self.invalidated.append(fcm_token)
        for tokens in self.tokens.values():
            if fcm_token in tokens:
                tokens.remove(fcm_token)

    def is_active(self, user_id: uuid.UUID) -> bool:
        return user_id not in self.inactive


class FakePush(PushSender):
    """Registra los envíos. `failures[token]` es cuántas veces falla antes de recibir."""

    def __init__(self, invalid: set[str] | None = None, failures: dict[str, int] | None = None) -> None:
        self.sent: list[tuple[str, str]] = []
        self.calls: list[str] = []
        self.invalid = invalid or set()
        self.failures = dict(failures or {})

    def send(self, token: str, message: str) -> None:
        self.calls.append(token)
        if token in self.invalid:
            raise InvalidPushTokenError()
        if self.failures.get(token, 0) > 0:
            self.failures[token] -= 1
            raise PushDeliveryError()
        self.sent.append((token, message))


def repository() -> InMemoryReminderRepository:
    return InMemoryReminderRepository()
