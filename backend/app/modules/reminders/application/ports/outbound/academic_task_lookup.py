"""Outbound port used by reminders to read minimal task data from the
Academic bounded context.

Design rule: reminders never imports Academic's domain (`Task`,
`TaskRepository`, etc.). Instead it defines its OWN small data
contract (`TaskSummary`) and depends only on that. Whoever implements
`AcademicTaskLookup` is responsible for mapping Academic's real Task
into this DTO. This is what DDD calls an Anti-Corruption Layer: the
translation happens on the Academic side of the boundary, never here.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TaskSummary:
    """Minimal, read-only view of an academic task, owned by reminders.

    This is NOT the `Task` entity from the academic module. It only
    carries what reminders needs to validate a reference and, later,
    to enrich a notification message.
    """

    task_id: int
    owner_user_id: UUID
    title: str
    due_date: datetime | None


class AcademicTaskLookup(ABC):
    """Outbound port of the reminders module toward Academic.

    Reminders only ever asks "does this task exist, and who owns it".
    It never asks Academic to create, update or delete anything.
    """

    @abstractmethod
    def get_summary(self, task_id: int) -> TaskSummary | None:
        """Returns a TaskSummary if the task exists, otherwise None."""
        raise NotImplementedError
