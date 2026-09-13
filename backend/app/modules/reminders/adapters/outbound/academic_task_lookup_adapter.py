from uuid import UUID
from backend.app.modules.reminders.application.ports.outbound.academic_task_lookup import AcademicTaskLookup, TaskSummary

class AcademicTaskLookupAdapter(AcademicTaskLookup):
    def __init__(self, get_summary):
        self._get_summary = get_summary

    def get_summary(self, task_id: UUID, user_id: UUID) -> TaskSummary | None:
        task = self._get_summary(task_id, user_id)
        if task is None:
            return None
        return TaskSummary(
            task_id=task.task_id,
            owner_user_id=task.owner_user_id,
            title=task.title,
            due_date=task.due_date,
        )