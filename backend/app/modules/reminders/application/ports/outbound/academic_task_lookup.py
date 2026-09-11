from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from uuid import UUID

@dataclass(frozen=True)
class TaskSummary:
    task_id: UUID
    owner_user_id: UUID
    title: str
    due_date: date | None

class AcademicTaskLookup(ABC):
    @abstractmethod
    def get_summary(self, task_id: UUID, user_id: UUID) -> TaskSummary | None:
        raise NotImplementedError
