"""Caso de uso para registrar un usuario."""

from __future__ import annotations

from app.modules.usuario.application.ports.outbound.password_hasher import PasswordHasher
from app.modules.usuario.application.ports.outbound.user_repository import UserRepository
from app.modules.usuario.domain.entities.usuario import Usuario
from app.modules.usuario.domain.value_objects.email import Email

# RF-USR-10: versión vigente de docs/politica_privacidad.md. Cambiar el texto de la
# política obliga a cambiar esta constante y la fecha de vigencia del documento.
CURRENT_POLICY_VERSION = "2026-11-v1"


class UserAlreadyExistsError(ValueError):
    """Se lanza cuando el correo ya pertenece a un usuario."""


class ConsentRequiredError(ValueError):
    """Se lanza cuando el registro no trae la aceptación de la política vigente."""


def check_consent(accepted: bool, policy_version: str) -> None:
    """Exige aceptación explícita de la versión vigente (RF-USR-10)."""

    if not accepted:
        raise ConsentRequiredError(
            "Debe aceptar la política de tratamiento de datos personales para registrarse."
        )
    if policy_version != CURRENT_POLICY_VERSION:
        raise ConsentRequiredError(
            f"La política cambió: debe aceptar la versión {CURRENT_POLICY_VERSION}."
        )


class RegisterUserUseCase:
    """Coordina creación, protección de contraseña y persistencia del usuario."""

    def __init__(self, repository: UserRepository, password_hasher: PasswordHasher) -> None:
        self._repository = repository
        self._password_hasher = password_hasher

    def execute(
        self,
        full_name: str,
        email: str,
        password: str,
        consent_accepted: bool,
        consent_policy_version: str,
    ) -> Usuario:
        check_consent(consent_accepted, consent_policy_version)

        email_value = Email(email)
        if self._repository.get_by_email(email_value) is not None:
            raise UserAlreadyExistsError("Ya existe un usuario con ese correo.")
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")

        password_hash = self._password_hasher.hash(password)
        user = Usuario.create(full_name=full_name, email=email_value, password_hash=password_hash)
        user.accept_policy(consent_policy_version)
        self._repository.add(user)
        return user
