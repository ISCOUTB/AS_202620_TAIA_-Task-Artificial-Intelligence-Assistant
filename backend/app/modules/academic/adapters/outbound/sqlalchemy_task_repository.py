"""Persistencia de tareas en PostgreSQL (tabla `tasks` del diccionario de datos)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import sessionmaker

from app.modules.academic.adapters.outbound.sqlalchemy_models import SubjectModel, TaskModel
from app.modules.academic.application.ports.outbound.task_repository import TaskQuery, TaskRepository
from app.modules.academic.domain.entities.task import Task, TaskStatus
from app.shared.clock import as_bogota


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, task: Task) -> None:
        with self._session_factory.begin() as session:
            session.add(_to_model(task))

    def save(self, task: Task) -> None:
        with self._session_factory.begin() as session:
            session.merge(_to_model(task))

    def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        query = _owned_by(user_id).where(TaskModel.id == task_id)
        with self._session_factory() as session:
            model = session.scalars(query).first()
            return _to_domain(model) if model is not None else None

    def list(self, user_id: uuid.UUID, query: TaskQuery, now: datetime) -> tuple[list[Task], int]:
        filtered = _apply_filters(_owned_by(user_id), query, now)
        page = filtered.order_by(TaskModel.due_at, TaskModel.id).limit(query.limit).offset(query.offset)
        with self._session_factory() as session:
            total = session.scalar(select(func.count()).select_from(filtered.subquery()))
            return [_to_domain(model) for model in session.scalars(page)], total

    def count_by_subject(self, subject_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(TaskModel).where(TaskModel.subject_id == subject_id)
        with self._session_factory() as session:
            return session.scalar(query)

    def count_open_by_subject(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        query = (
            select(TaskModel.subject_id, func.count())
            .join(SubjectModel, SubjectModel.id == TaskModel.subject_id)
            .where(
                SubjectModel.user_id == user_id,
                TaskModel.deleted_at.is_(None),
                TaskModel.completed_at.is_(None),
            )
            .group_by(TaskModel.subject_id)
        )
        with self._session_factory() as session:
            return {subject_id: count for subject_id, count in session.execute(query)}


def _owned_by(user_id: uuid.UUID) -> Select:
    """Tareas no eliminadas cuyo propietario (a través de la asignatura) es el usuario."""

    return (
        select(TaskModel)
        .join(SubjectModel, SubjectModel.id == TaskModel.subject_id)
        .where(SubjectModel.user_id == user_id, TaskModel.deleted_at.is_(None))
    )


def _apply_filters(query: Select, filters: TaskQuery, now: datetime) -> Select:
    if filters.subject_id is not None:
        query = query.where(TaskModel.subject_id == filters.subject_id)
    if filters.status is TaskStatus.COMPLETED:
        query = query.where(TaskModel.completed_at.is_not(None))
    elif filters.status is TaskStatus.PENDING:
        query = query.where(TaskModel.completed_at.is_(None), TaskModel.due_at >= now)
    elif filters.status is TaskStatus.OVERDUE:
        query = query.where(TaskModel.completed_at.is_(None), TaskModel.due_at < now)
    if filters.type is not None:
        query = query.where(TaskModel.type == filters.type)
    if filters.due_from is not None:
        query = query.where(TaskModel.due_at >= filters.due_from)
    if filters.due_to is not None:
        query = query.where(TaskModel.due_at <= filters.due_to)
    if filters.text:
        query = query.where(
            or_(
                TaskModel.title.icontains(filters.text, autoescape=True),
                TaskModel.description.icontains(filters.text, autoescape=True),
            )
        )
    return query


def _to_model(task: Task) -> TaskModel:
    return TaskModel(
        id=task.id,
        subject_id=task.subject_id,
        type=task.type,
        title=task.title,
        description=task.description,
        due_at=task.due_at,
        completed_at=task.completed_at,
        deleted_at=task.deleted_at,
        created_at=task.created_at,
    )


def _to_domain(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        subject_id=model.subject_id,
        type=model.type,
        title=model.title,
        description=model.description,
        due_at=as_bogota(model.due_at),
        completed_at=as_bogota(model.completed_at) if model.completed_at else None,
        deleted_at=as_bogota(model.deleted_at) if model.deleted_at else None,
        created_at=as_bogota(model.created_at),
    )
