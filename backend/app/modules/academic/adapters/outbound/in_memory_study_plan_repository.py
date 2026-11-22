"""Repositorio en memoria de los planes de estudio, para las pruebas unitarias."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime

from app.modules.academic.application.ports.outbound.study_plan_repository import StudyPlanRepository
from app.modules.academic.domain.entities.study_plan import StudyPlan, StudyPlanStatus, StudySession

PROPOSED, ACCEPTED, DISCARDED = StudyPlanStatus.PROPOSED, StudyPlanStatus.ACCEPTED, StudyPlanStatus.DISCARDED


class InMemoryStudyPlanRepository(StudyPlanRepository):
    def __init__(self) -> None:
        self.plans: dict[uuid.UUID, StudyPlan] = {}

    def add(self, plan: StudyPlan) -> None:
        self._set(plan.user_id, PROPOSED, DISCARDED)
        self.plans[plan.id] = replace(plan, unscheduled_task_ids=[])

    def get(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> StudyPlan | None:
        plan = self.plans.get(plan_id)
        return plan if plan is not None and plan.user_id == user_id else None

    def current(self, user_id: uuid.UUID) -> StudyPlan | None:
        own = [plan for plan in self.plans.values() if plan.user_id == user_id]
        for status in (PROPOSED, ACCEPTED):
            matching = [plan for plan in own if plan.status is status]
            if matching:
                return matching[-1]
        return None

    def accept(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        plan = self.get(plan_id, user_id)
        if plan is None or plan.status is not PROPOSED:
            return False
        self._set(user_id, ACCEPTED, DISCARDED)
        plan.status = ACCEPTED
        return True

    def discard(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        plan = self.get(plan_id, user_id)
        if plan is None or plan.status is DISCARDED:
            return False
        plan.status = DISCARDED
        return True

    def accepted_sessions(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[StudySession]:
        return sorted(
            (
                session
                for plan in self.plans.values()
                if plan.user_id == user_id and plan.status is ACCEPTED
                for session in plan.sessions
                if start <= session.starts_at < end
            ),
            key=lambda session: session.starts_at,
        )

    def _set(self, user_id: uuid.UUID, current: StudyPlanStatus, new: StudyPlanStatus) -> None:
        for plan in self.plans.values():
            if plan.user_id == user_id and plan.status is current:
                plan.status = new
