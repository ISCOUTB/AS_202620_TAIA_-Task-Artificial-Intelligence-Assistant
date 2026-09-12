"""Caso de uso para registrar un usuario."""

from __future__ import annotations

from backend.app.modules.usuario.application.ports.outbound.password_hasher import PasswordHasher
from backend.app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from backend.app.modules.usuario.domain.entities.usuario import Usuario
from backend.app.modules.usuario.domain.value_objects.email import Email


class UserAlreadyExistsError(ValueError):
    """Se lanza cuando el correo ya pertenece a un usuario."""


class RegisterUserUseCase:
    """Coordina creación, protección de contraseña y persistencia del usuario."""

    def __init__(self, repository: UserRepository, password_hasher: PasswordHasher) -> None:
        self._repository = repository
        self._password_hasher = password_hasher

    def execute(self, name: str, email: str, password: str) -> Usuario:
        email_value = Email(email)
        if self._repository.get_by_email(email_value) is not None:
            raise UserAlreadyExistsError("Ya existe un usuario con ese correo.")
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")

        password_hash = self._password_hasher.hash(password)
        user = Usuario.create(name=name, email=email_value, password_hash=password_hash)
        self._repository.add(user)
        return user
