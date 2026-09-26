"""Composición de los repositorios del módulo académico."""

from app.modules.academic.adapters.outbound.in_memory_structure_repositories import (
    InMemoryAcademicPeriodRepository,
    InMemoryScheduleBlockRepository,
    InMemorySubjectRepository,
)
from app.modules.academic.adapters.outbound.sqlalchemy_structure_repositories import (
    SqlAlchemyAcademicPeriodRepository,
    SqlAlchemyScheduleBlockRepository,
    SqlAlchemySubjectRepository,
)
from app.modules.academic.adapters.outbound.in_memory_task_repository import (
    InMemoryTaskRepository,
)
from app.modules.academic.adapters.outbound.sqlalchemy_task_repository import SqlAlchemyTaskRepository
from app.modules.academic.application.ports.outbound.academic_period_repository import (
    AcademicPeriodRepository,
)
from app.modules.academic.application.ports.outbound.schedule_block_repository import (
    ScheduleBlockRepository,
)
from app.modules.academic.application.ports.outbound.subject_repository import SubjectRepository
from app.modules.academic.application.ports.outbound.task_repository import TaskRepository
from app.shared.adapters.outbound.database import get_session_factory, use_in_memory_storage


if use_in_memory_storage():
    _subjects: SubjectRepository = InMemorySubjectRepository()
    _blocks: ScheduleBlockRepository = InMemoryScheduleBlockRepository(_subjects)
    _periods: AcademicPeriodRepository = InMemoryAcademicPeriodRepository()
    _repository: TaskRepository = InMemoryTaskRepository(_subjects)
else:
    _subjects = SqlAlchemySubjectRepository(get_session_factory())
    _blocks = SqlAlchemyScheduleBlockRepository(get_session_factory())
    _periods = SqlAlchemyAcademicPeriodRepository(get_session_factory())
    _repository = SqlAlchemyTaskRepository(get_session_factory())


def get_task_repository() -> TaskRepository:
    """Devuelve la instancia compartida del repositorio académico."""

    return _repository


def get_subject_repository() -> SubjectRepository:
    return _subjects


def get_schedule_block_repository() -> ScheduleBlockRepository:
    return _blocks


def get_academic_period_repository() -> AcademicPeriodRepository:
    return _periods
