"""Casos de uso de la cuenta del usuario autenticado (RF-USR-06, 07)."""

from __future__ import annotations

import uuid

from app.modules.usuario.application.ports.outbound.password_hasher import PasswordHasher
from app.modules.usuario.application.ports.outbound.session_repository import SessionRepository
from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.modules.usuario.application.use_cases.get_current_user import AuthenticatedUserNotFoundError
from app.modules.usuario.application.use_cases.register_user import (
    UserAlreadyExistsError,
    WeakPasswordError,
    check_password_rules,
)
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email
from app.shared.clock import Clock, now_bogota


class IncorrectPasswordError(ValueError):
    """La contraseña actual falta o no coincide."""


def check_current_password(hasher: PasswordHasher, user: Usuario, password: str | None) -> None:
    """Exige la contraseña actual antes de una operación sensible de la cuenta."""
    if not password or not hasher.verify(password, user.password_hash):
        raise IncorrectPasswordError("La contraseña actual es incorrecta.")


def _get_user(users: UserRepository, user_id: uuid.UUID) -> Usuario:
    user = users.get_by_id(user_id)
    if user is None:
        raise AuthenticatedUserNotFoundError("Usuario autenticado no encontrado.")
    return user


class UpdateProfileUseCase:
    """Actualiza el nombre y el correo; cambiar el correo exige la contraseña (RF-USR-06)."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    def execute(
        self,
        user_id: uuid.UUID,
        full_name: str | None = None,
        email: str | None = None,
        current_password: str | None = None,
    ) -> Usuario:
        user = _get_user(self._users, user_id)
        if full_name is not None:
            user.rename(full_name)
        if email is not None:
            new_email = Email(email)
            if new_email != user.email:
                # La contraseña va antes que la unicidad: sin ella no se revela qué correos existen.
                check_current_password(self._hasher, user, current_password)
                if self._users.get_by_email(new_email) is not None:
                    raise UserAlreadyExistsError("Ya existe un usuario con ese correo.")
                user.change_email(new_email)
        self._users.save(user)
        return user


class ChangePasswordUseCase:
    """Cambia la contraseña y revoca las demás sesiones del usuario (RF-USR-07)."""

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        sessions: SessionRepository,
        now: Clock = now_bogota,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._sessions = sessions
        self._now = now

    def execute(
        self, user_id: uuid.UUID, session_id: uuid.UUID, current_password: str, new_password: str
    ) -> None:
        user = _get_user(self._users, user_id)
        check_current_password(self._hasher, user, current_password)
        check_password_rules(new_password)
        if self._hasher.verify(new_password, user.password_hash):
            raise WeakPasswordError("La nueva contraseña debe ser distinta de la actual.")

        user.password_hash = self._hasher.hash(new_password)
        self._users.save(user)
        self._sessions.revoke_others(user.id, session_id, self._now())
