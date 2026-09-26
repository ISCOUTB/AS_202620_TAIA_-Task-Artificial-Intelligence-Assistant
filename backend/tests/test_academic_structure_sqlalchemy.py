"""Pruebas de integración de asignaturas, horario y período contra PostgreSQL (RNF-06).

Usan la fixture `clean_db` de conftest.py; sin TEST_DATABASE_URL se omiten.
"""

from __future__ import annotations

import uuid
from datetime import date, time

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.academic.adapters.outbound.sqlalchemy_structure_repositories import (
    SqlAlchemyAcademicPeriodRepository,
    SqlAlchemyScheduleBlockRepository,
    SqlAlchemySubjectRepository,
)
from app.modules.academic.domain.entities.academic_period import AcademicPeriod
from app.modules.academic.domain.entities.schedule_block import ScheduleBlock, Weekday
from app.modules.academic.domain.entities.subject import Subject

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()


@pytest.fixture
def subjects(clean_db):
    return SqlAlchemySubjectRepository(clean_db)


@pytest.fixture
def blocks(clean_db):
    return SqlAlchemyScheduleBlockRepository(clean_db)


def test_subject_round_trip_with_aliases(subjects):
    subject = Subject.create(USER, "Matemáticas Básicas", "Ana")
    subject.add_alias("Mate básicas")
    subjects.add(subject)

    stored = subjects.get(subject.id, USER)

    assert stored.name == "Matemáticas Básicas"
    assert stored.normalized_name == "matematicas basicas"
    assert [alias.alias for alias in stored.aliases] == ["Mate básicas"]
    assert subjects.get(subject.id, OTHER_USER) is None


def test_save_adds_and_removes_aliases(subjects):
    subject = Subject.create(USER, "Física")
    first = subject.add_alias("Fis")
    subjects.add(subject)

    subject.remove_alias(first.id)
    subject.add_alias("Física I")
    subjects.save(subject)

    assert [alias.alias for alias in subjects.get(subject.id, USER).aliases] == ["Física I"]


def test_normalized_name_is_unique_per_user(subjects):
    subjects.add(Subject.create(USER, "Física"))
    subjects.add(Subject.create(OTHER_USER, "Física"))

    with pytest.raises(IntegrityError):
        subjects.add(Subject.create(USER, "FÍSICA"))


def test_list_excludes_archived_and_orders_by_name(subjects):
    quimica = Subject.create(USER, "Química")
    algebra = Subject.create(USER, "Álgebra")
    historia = Subject.create(USER, "Historia")
    historia.archive()
    for subject in (quimica, algebra, historia):
        subjects.add(subject)

    assert [s.name for s in subjects.list_by_user(USER)] == ["Álgebra", "Química"]
    assert len(subjects.list_by_user(USER, include_archived=True)) == 3


def test_blocks_are_sorted_by_weekday_enum_and_hidden_when_archived(subjects, blocks):
    physics = Subject.create(USER, "Física")
    history = Subject.create(USER, "Historia")
    subjects.add(physics)
    subjects.add(history)
    blocks.add(ScheduleBlock.create(physics.id, Weekday.FRIDAY, time(8), time(10)))
    blocks.add(ScheduleBlock.create(physics.id, Weekday.MONDAY, time(10), time(12)))
    blocks.add(ScheduleBlock.create(physics.id, Weekday.MONDAY, time(7), time(9)))
    blocks.add(ScheduleBlock.create(history.id, Weekday.TUESDAY, time(7), time(9)))

    history.archive()
    subjects.save(history)

    listed = blocks.list_by_user(USER)
    assert [(b.weekday, b.start_time) for b in listed] == [
        (Weekday.MONDAY, time(7)),
        (Weekday.MONDAY, time(10)),
        (Weekday.FRIDAY, time(8)),
    ]
    assert [b.weekday for b in blocks.list_by_user(USER, weekday=Weekday.FRIDAY)] == [Weekday.FRIDAY]
    assert blocks.list_by_user(OTHER_USER) == []


def test_deleting_subject_cascades_to_blocks_and_aliases(subjects, blocks):
    subject = Subject.create(USER, "Biología")
    subject.add_alias("Bio")
    subjects.add(subject)
    block = ScheduleBlock.create(subject.id, Weekday.MONDAY, time(8), time(10))
    blocks.add(block)

    subjects.delete(subject.id)

    assert subjects.get(subject.id, USER) is None
    assert blocks.get(block.id, USER) is None


def test_block_update_and_ownership(subjects, blocks):
    subject = Subject.create(USER, "Física")
    subjects.add(subject)
    block = ScheduleBlock.create(subject.id, Weekday.MONDAY, time(8), time(10), "A-1")
    blocks.add(block)

    block.update(weekday=Weekday.THURSDAY, room="B-2")
    blocks.save(block)

    stored = blocks.get(block.id, USER)
    assert (stored.weekday, stored.room) == (Weekday.THURSDAY, "B-2")
    assert blocks.get(block.id, OTHER_USER) is None


def test_academic_period_is_replaced(clean_db):
    periods = SqlAlchemyAcademicPeriodRepository(clean_db)
    periods.save(AcademicPeriod(USER, date(2026, 2, 1), date(2026, 6, 1)))
    periods.save(AcademicPeriod(USER, date(2026, 8, 1), date(2026, 12, 5)))

    assert periods.get(USER) == AcademicPeriod(USER, date(2026, 8, 1), date(2026, 12, 5))
    assert periods.get(OTHER_USER) is None
