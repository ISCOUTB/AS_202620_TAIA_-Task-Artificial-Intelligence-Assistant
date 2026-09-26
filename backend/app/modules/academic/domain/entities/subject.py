"""Asignaturas del estudiante y sus alias (RF-ASG-01…05, RF-ASG-09)."""

from __future__ import annotations

import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.shared.clock import now_bogota


class InvalidSubjectError(ValueError):
    """Los datos de la asignatura violan una regla del dominio."""


def normalize_text(value: str) -> str:
    """Minúsculas, sin tildes y con espacios simples: "Matemáticas  Básicas" -> "matematicas basicas"."""

    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.lower().split())


@dataclass
class SubjectAlias:
    id: uuid.UUID
    alias: str
    normalized_alias: str

    MAX_LENGTH = 50


@dataclass
class Subject:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    normalized_name: str
    teacher: str | None = None
    archived_at: datetime | None = None
    aliases: list[SubjectAlias] = field(default_factory=list)
    created_at: datetime = field(default_factory=now_bogota)

    MAX_NAME_LENGTH = 100
    MAX_TEACHER_LENGTH = 100

    @staticmethod
    def create(user_id: uuid.UUID, name: str, teacher: str | None = None) -> "Subject":
        clean_name = _clean_name(name)
        return Subject(
            id=uuid.uuid4(),
            user_id=user_id,
            name=clean_name,
            normalized_name=normalize_text(clean_name),
            teacher=_clean_teacher(teacher),
        )

    @property
    def archived(self) -> bool:
        return self.archived_at is not None

    def rename(self, name: str) -> None:
        self.name = _clean_name(name)
        self.normalized_name = normalize_text(self.name)

    def set_teacher(self, teacher: str | None) -> None:
        self.teacher = _clean_teacher(teacher)

    def archive(self, now: datetime | None = None) -> None:
        if self.archived_at is None:
            self.archived_at = now or now_bogota()

    def unarchive(self) -> None:
        self.archived_at = None

    def add_alias(self, alias: str) -> SubjectAlias:
        clean_alias = " ".join((alias or "").split())
        if not clean_alias:
            raise InvalidSubjectError("El alias no puede estar vacío.")
        if len(clean_alias) > SubjectAlias.MAX_LENGTH:
            raise InvalidSubjectError(f"El alias no puede superar {SubjectAlias.MAX_LENGTH} caracteres.")
        normalized = normalize_text(clean_alias)
        if any(existing.normalized_alias == normalized for existing in self.aliases):
            raise InvalidSubjectError("La asignatura ya tiene ese alias.")
        created = SubjectAlias(id=uuid.uuid4(), alias=clean_alias, normalized_alias=normalized)
        self.aliases.append(created)
        return created

    def remove_alias(self, alias_id: uuid.UUID) -> bool:
        remaining = [alias for alias in self.aliases if alias.id != alias_id]
        removed = len(remaining) != len(self.aliases)
        self.aliases = remaining
        return removed


def _clean_name(name: str) -> str:
    clean = " ".join((name or "").split())
    if not clean:
        raise InvalidSubjectError("El nombre de la asignatura no puede estar vacío.")
    if len(clean) > Subject.MAX_NAME_LENGTH:
        raise InvalidSubjectError(f"El nombre no puede superar {Subject.MAX_NAME_LENGTH} caracteres.")
    return clean


def _clean_teacher(teacher: str | None) -> str | None:
    clean = " ".join((teacher or "").split())
    if len(clean) > Subject.MAX_TEACHER_LENGTH:
        raise InvalidSubjectError(f"El docente no puede superar {Subject.MAX_TEACHER_LENGTH} caracteres.")
    return clean or None
