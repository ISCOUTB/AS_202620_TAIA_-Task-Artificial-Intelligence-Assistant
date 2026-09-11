"""Outbound adapter: implementation of AcademicTaskLookup.

Since TAIA is a modular monolith, this adapter calls Academic's own
public use case / repository in-process (no HTTP). It is the ONLY
place in reminders that is allowed to import anything from the
academic module, and it does so only to translate Academic's real
Task into reminders' own TaskSummary DTO. This isolates the coupling
to a single, obvious file (Anti-Corruption Layer).
"""

from app.modules.reminders.application.ports.outbound.academic_task_lookup import (
    AcademicTaskLookup,
    TaskSummary,
)

# from app.modules.academic.application.use_cases.get_task import GetTaskUseCase


class AcademicTaskLookupAdapter(AcademicTaskLookup):
    def __init__(self, get_task_use_case):
        """
        get_task_use_case: Academic's own read-only use case/service
        that returns a task by id (e.g. GetTaskUseCase from the
        academic module). Injected here so reminders never imports
        Academic's repository or ORM models directly.
        """
        self._get_task_use_case = get_task_use_case

    def get_summary(self, task_id: int) -> TaskSummary | None:
        task = self._get_task_use_case.execute(task_id)
        if task is None:
            return None

        return TaskSummary(
            task_id=task.id,
            owner_user_id=task.user_id,
            title=task.title,
            due_date=getattr(task, "due_date", None),
        )
