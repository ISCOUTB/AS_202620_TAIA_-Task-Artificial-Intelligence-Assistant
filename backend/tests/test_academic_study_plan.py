"""Plan de estudio: formulario, reglas del backend, aceptar y calendario (RF-EST-01…03, RT-02)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.academic.adapters.outbound.in_memory_structure_repositories import (
    InMemoryAcademicPeriodRepository,
    InMemoryScheduleBlockRepository,
    InMemorySubjectRepository,
)
from app.modules.academic.adapters.outbound.in_memory_study_plan_repository import InMemoryStudyPlanRepository
from app.modules.academic.adapters.outbound.in_memory_task_repository import InMemoryTaskRepository
from app.modules.academic.application.errors import StudyPlanNotFoundError, StudyPlanStateError
from app.modules.academic.application.study_planner import FreeSlot, PlanItem, free_slots, place_sessions
from app.modules.academic.application.use_cases.academic_calendar import AcademicCalendarUseCase
from app.modules.academic.application.use_cases.manage_study_plan import ManageStudyPlanUseCase
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.study_plan import (
    BusyBlock,
    BusyBlockKind,
    InvalidStudyPlanError,
    StudyPlanStatus,
    StudyPreference,
    StudyPreferences,
    StudyTimePreference,
)
from app.modules.academic.domain.entities.subject import Subject
from app.modules.academic.domain.entities.task import Task
from app.modules.ai.application.ports.inbound import study_plan_advisor
from app.shared.clock import BOGOTA_TZ
from tests.helpers import create_subject, register_and_login

# Lunes 1 de marzo de 2027 a las 07:00.
MONDAY = date(2027, 3, 1)
NOW = datetime(2027, 3, 1, 7, 0, tzinfo=BOGOTA_TZ)


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=BOGOTA_TZ)


class FakeAdvisor:
    def __init__(self, proposals: list[tuple[int, int]] | None = None) -> None:
        self.proposals = proposals or []
        self.calls: list[tuple[list, list]] = []

    def propose(self, slots, items):
        self.calls.append((list(slots), list(items)))
        return self.proposals


class World:
    def __init__(self, advisor: FakeAdvisor | None = None) -> None:
        self.owner = uuid.uuid4()
        self.subjects = InMemorySubjectRepository()
        self.tasks = InMemoryTaskRepository(self.subjects)
        self.blocks = InMemoryScheduleBlockRepository(self.subjects)
        self.periods = InMemoryAcademicPeriodRepository()
        self.plans = InMemoryStudyPlanRepository()
        self.advisor = advisor or FakeAdvisor()
        calendar = AcademicCalendarUseCase(self.tasks, self.subjects, self.blocks, self.periods, clock=lambda: NOW)
        self.use_case = ManageStudyPlanUseCase(
            self.plans, self.tasks, self.subjects, calendar, self.advisor, clock=lambda: NOW
        )

    def subject(self, name: str) -> Subject:
        subject = Subject.create(self.owner, name)
        self.subjects.add(subject)
        return subject

    def task(self, subject: Subject, title: str, due_at: datetime) -> Task:
        task = Task.create(subject.id, title, due_at, now=NOW - timedelta(days=1))
        self.tasks.add(task)
        return task

    def block(self, subject: Subject, weekday: Weekday, start: time, end: time) -> None:
        self.blocks.add(ScheduleBlock.create(subject.id, weekday, start, end))


@pytest.fixture
def world() -> World:
    return World()


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


# -- RF-EST-01: formulario ----------------------------------------------------


@pytest.mark.parametrize("start, end", [(time(4, 0), time(10, 0)), (time(6, 0), time(23, 30)), (time(10), time(9))])
def test_window_outside_limits_is_rejected_rf_est_01(start, end):
    with pytest.raises(InvalidStudyPlanError):
        StudyPreferences(preference=StudyPreference.BOTH, window_start=start, window_end=end)


def test_defaults_use_every_day_and_every_active_subject_rf_est_01(world):
    physics, math = world.subject("Física"), world.subject("Cálculo")

    plan = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH, days=frozenset()))

    assert plan.preferences.days == frozenset(Weekday)
    assert set(plan.preferences.subject_ids) == {physics.id, math.id}
    assert (plan.preferences.window_start, plan.preferences.window_end) == (time(6), time(22))
    assert plan.preferences.session_minutes == 60


def test_max_daily_minutes_cannot_be_less_than_a_session_rf_est_01():
    with pytest.raises(InvalidStudyPlanError):
        StudyPreferences(preference=StudyPreference.BOTH, session_minutes=60, max_daily_minutes=30)


# -- RF-EST-02: reglas del backend --------------------------------------------


def test_sessions_never_overlap_classes_work_or_each_other_rf_est_02(world):
    physics = world.subject("Física")
    world.block(physics, Weekday.MONDAY, time(8), time(12))
    world.block(physics, Weekday.TUESDAY, time(14), time(16))
    for days in range(1, 7):
        world.task(physics, f"Taller {days}", _at(MONDAY + timedelta(days=days), 23, 59))
    work = BusyBlock(BusyBlockKind.WORK, Weekday.MONDAY, time(13), time(18))

    plan = world.use_case.generate(
        world.owner, StudyPreferences(preference=StudyPreference.BOTH, busy_blocks=(work,))
    )

    assert plan.sessions
    busy = [
        (_at(MONDAY, 8), _at(MONDAY, 12)),
        (_at(MONDAY + timedelta(days=1), 14), _at(MONDAY + timedelta(days=1), 16)),
        (_at(MONDAY + timedelta(days=7), 8), _at(MONDAY + timedelta(days=7), 12)),
        (_at(MONDAY, 13), _at(MONDAY, 18)),
    ]
    for session in plan.sessions:
        assert not any(_overlaps(session.starts_at, session.ends_at, a, b) for a, b in busy)
        assert session.starts_at >= NOW
    ordered = sorted(plan.sessions, key=lambda s: s.starts_at)
    for previous, following in zip(ordered, ordered[1:]):
        assert previous.ends_at <= following.starts_at


def test_sessions_stay_inside_window_and_allowed_days_rf_est_02(world):
    physics = world.subject("Física")
    for days in range(1, 7):
        world.task(physics, f"Lectura {days}", _at(MONDAY + timedelta(days=days), 23, 59))
    prefs = StudyPreferences(
        preference=StudyPreference.BOTH,
        days=frozenset({Weekday.TUESDAY, Weekday.THURSDAY}),
        window_start=time(18),
        window_end=time(21),
    )

    plan = world.use_case.generate(world.owner, prefs)

    assert plan.sessions
    for session in plan.sessions:
        assert list(Weekday)[session.starts_at.weekday()] in prefs.days
        assert time(18) <= session.starts_at.time() and session.ends_at.time() <= time(21)


def test_no_session_after_the_due_date_rf_est_02(world):
    physics = world.subject("Física")
    task = world.task(physics, "Quiz", _at(MONDAY, 12))

    plan = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))

    sessions = [s for s in plan.sessions if s.task_id == task.id]
    assert sessions and all(s.ends_at <= _at(MONDAY, 12) for s in sessions)


def test_task_that_does_not_fit_is_reported_rf_est_02(world):
    physics = world.subject("Física")
    task = world.task(physics, "Para ya", _at(MONDAY, 7, 30))

    plan = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))

    assert task.id in plan.unscheduled_task_ids
    assert not any(s.task_id == task.id for s in plan.sessions)


def test_high_priority_goes_first_and_gets_two_sessions_rf_est_02():
    slots = [FreeSlot(i, _at(MONDAY + timedelta(days=i), 18), _at(MONDAY + timedelta(days=i), 19)) for i in range(2)]
    urgent = PlanItem(0, uuid.uuid4(), uuid.uuid4(), "Parcial", "Física", _at(MONDAY + timedelta(days=1), 23), "high")
    later = PlanItem(1, uuid.uuid4(), uuid.uuid4(), "Ensayo", "Inglés", _at(MONDAY + timedelta(days=20), 23), "low")
    prefs = StudyPreferences(preference=StudyPreference.BOTH)

    # El LLM pone primero la de prioridad baja; la regla manda.
    placement = place_sessions(prefs, slots, [later, urgent], proposals=[(1, 0), (0, 1)])

    assert [s.task_id for s in placement.sessions] == [urgent.task_id, urgent.task_id]
    assert placement.unscheduled_task_ids == [later.task_id]


def test_invalid_llm_proposals_are_discarded_or_relocated_rf_est_02():
    slots = [FreeSlot(0, _at(MONDAY, 18), _at(MONDAY, 19)), FreeSlot(1, _at(MONDAY + timedelta(days=3), 18), _at(MONDAY + timedelta(days=3), 19))]
    item = PlanItem(0, uuid.uuid4(), uuid.uuid4(), "Taller", "Física", _at(MONDAY, 23), "medium")
    prefs = StudyPreferences(preference=StudyPreference.BOTH)

    # Hueco después de la fecha límite, hueco inventado y actividad inventada.
    placement = place_sessions(prefs, slots, [item], proposals=[(0, 1), (0, 99), (7, 0)])

    assert [(s.task_id, s.starts_at) for s in placement.sessions] == [(item.task_id, _at(MONDAY, 18))]


def test_max_daily_minutes_is_respected_rf_est_02(world):
    physics = world.subject("Física")
    for n in range(6):
        world.task(physics, f"Taller {n}", _at(MONDAY, 23, 59))

    plan = world.use_case.generate(
        world.owner, StudyPreferences(preference=StudyPreference.BOTH, max_daily_minutes=120)
    )

    per_day: dict[date, int] = {}
    for session in plan.sessions:
        per_day[session.starts_at.date()] = per_day.get(session.starts_at.date(), 0) + 60
    assert per_day[MONDAY] == 120


def test_preferred_time_is_used_first_but_not_required_rf_est_02(world):
    physics = world.subject("Física")
    task = world.task(physics, "Lectura", _at(MONDAY + timedelta(days=5), 23, 59))

    plan = world.use_case.generate(
        world.owner, StudyPreferences(preference=StudyPreference.BOTH, preferred_time=StudyTimePreference.EVENING)
    )

    session = next(s for s in plan.sessions if s.task_id == task.id)
    assert session.starts_at.time() >= time(18)


def test_between_classes_only_uses_gaps_between_classes_rf_est_02(world):
    physics = world.subject("Física")
    world.block(physics, Weekday.MONDAY, time(8), time(10))
    world.block(physics, Weekday.MONDAY, time(13), time(15))

    slots = free_slots(
        StudyPreferences(preference=StudyPreference.BETWEEN_CLASSES), NOW, MONDAY,
        [(_at(MONDAY, 8), _at(MONDAY, 10)), (_at(MONDAY, 13), _at(MONDAY, 15))],
    )

    assert [(s.starts_at, s.ends_at) for s in slots] == [
        (_at(MONDAY, 10), _at(MONDAY, 11)), (_at(MONDAY, 11), _at(MONDAY, 12)), (_at(MONDAY, 12), _at(MONDAY, 13)),
    ]


def test_plan_is_generated_without_the_llm_rf_est_02_rf_agt_20(world):
    physics = world.subject("Física")
    task = world.task(physics, "Informe", _at(MONDAY + timedelta(days=3), 23, 59))

    plan = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))

    assert any(s.task_id == task.id for s in plan.sessions)


def test_llm_receives_no_identifiers_rf_agt_17():
    advisor = FakeAdvisor()
    world = World(advisor)
    physics = world.subject("Física")
    task = world.task(physics, "Informe", _at(MONDAY + timedelta(days=3), 23, 59))

    world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))

    from app.modules.academic.adapters.outbound.ai_study_session_advisor import AiStudySessionAdvisor

    sent: list = []

    class Capture:
        def propose(self, slots, items):
            sent.extend(items)
            return []

    previous = study_plan_advisor._service
    study_plan_advisor.configure_study_plan_advisor(Capture())
    try:
        slots, items = advisor.calls[0]
        AiStudySessionAdvisor().propose(slots, items)
    finally:
        study_plan_advisor._service = previous
    text = repr(sent)
    assert str(task.id) not in text and str(world.owner) not in text and str(physics.id) not in text
    assert "Informe" in text


def test_subject_without_pending_tasks_gets_a_general_session_rf_est_02(world):
    physics = world.subject("Física")

    plan = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))

    assert [s.subject_id for s in plan.sessions] == [physics.id]


# -- RF-EST-03: consultar, aceptar, regenerar ---------------------------------


def test_generating_again_discards_the_previous_proposal_rf_est_03(world):
    world.subject("Física")
    first = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))
    second = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.AFTER_CLASSES))

    assert world.plans.get(first.id, world.owner).status is StudyPlanStatus.DISCARDED
    assert world.use_case.current(world.owner).id == second.id


def test_accepting_a_second_plan_discards_the_first_rf_est_03(world):
    world.subject("Física")
    first = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))
    world.use_case.accept(world.owner, first.id)
    second = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))

    world.use_case.accept(world.owner, second.id)

    assert world.plans.get(first.id, world.owner).status is StudyPlanStatus.DISCARDED
    assert world.plans.get(second.id, world.owner).status is StudyPlanStatus.ACCEPTED


def test_only_a_proposed_plan_can_be_accepted_rf_est_03(world):
    world.subject("Física")
    plan = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))
    world.use_case.discard(world.owner, plan.id)

    with pytest.raises(StudyPlanStateError):
        world.use_case.accept(world.owner, plan.id)


def test_other_users_plan_is_not_found_rt_02(world):
    world.subject("Física")
    plan = world.use_case.generate(world.owner, StudyPreferences(preference=StudyPreference.BOTH))

    with pytest.raises(StudyPlanNotFoundError):
        world.use_case.accept(uuid.uuid4(), plan.id)


# -- API y PostgreSQL ---------------------------------------------------------

client = TestClient(app)


@pytest.fixture
def fake_advisor():
    """Ninguna prueba llama a un LLM real: el asesor de AI se reemplaza."""

    previous = study_plan_advisor._service
    study_plan_advisor.configure_study_plan_advisor(FakeAdvisor())
    yield
    study_plan_advisor._service = previous


def test_api_generates_accepts_and_shows_sessions_in_the_calendar_rf_est_03(clean_db, fake_advisor):
    headers = register_and_login(client)
    subject_id = create_subject(client, headers, "Física")
    work = {"kind": "work", "weekday": "saturday", "start_time": "08:00:00", "end_time": "14:00:00"}

    created = client.post(
        "/academic/study-plans",
        json={"preference": "both", "busy_blocks": [work], "max_daily_minutes": 120, "preferred_time": "evening"},
        headers=headers,
    )

    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "proposed"
    assert body["busy_blocks"] == [work]
    assert body["subject_ids"] == [subject_id]
    assert body["sessions"] and body["sessions"][0]["title"] == "Repaso general"

    current = client.get("/academic/study-plans/current", headers=headers)
    assert current.json()["id"] == body["id"]

    accepted = client.post(f"/academic/study-plans/{body['id']}/accept", headers=headers)
    assert accepted.status_code == 200 and accepted.json()["status"] == "accepted"

    first = datetime.fromisoformat(body["sessions"][0]["starts_at"]).date()
    calendar = client.get(
        "/academic/calendar", params={"start": first.isoformat(), "end": first.isoformat()}, headers=headers
    )
    assert [s["id"] for s in calendar.json()["study_sessions"]] == [body["sessions"][0]["id"]]


def test_api_rejects_a_window_outside_limits_with_422_rf_est_01(clean_db, fake_advisor):
    headers = register_and_login(client)
    create_subject(client, headers, "Física")

    response = client.post(
        "/academic/study-plans", json={"preference": "both", "window_start": "04:00:00"}, headers=headers
    )

    assert response.status_code == 422


def test_api_accepting_twice_returns_409_rf_est_03(clean_db, fake_advisor):
    headers = register_and_login(client)
    create_subject(client, headers, "Física")
    plan = client.post("/academic/study-plans", json={"preference": "both"}, headers=headers).json()
    client.post(f"/academic/study-plans/{plan['id']}/accept", headers=headers)

    assert client.post(f"/academic/study-plans/{plan['id']}/accept", headers=headers).status_code == 409


def test_api_other_users_plan_returns_404_rt_02(clean_db, fake_advisor):
    owner = register_and_login(client)
    create_subject(client, owner, "Física")
    plan = client.post("/academic/study-plans", json={"preference": "both"}, headers=owner).json()
    stranger = register_and_login(client)

    assert client.post(f"/academic/study-plans/{plan['id']}/accept", headers=stranger).status_code == 404
    assert client.get("/academic/study-plans/current", headers=stranger).status_code == 404


def test_api_requires_authentication_rt_01():
    assert client.post("/academic/study-plans", json={"preference": "both"}).status_code == 401
