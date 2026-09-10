"""Value object para correos electrónicos del dominio Usuario."""

from __future__ import annotations

from dataclasses import dataclass


class InvalidEmailError(ValueError):
    """Se lanza cuando un correo no cumple las reglas mínimas del dominio."""


@dataclass(frozen=True)
class Email:
    """Correo electrónico normalizado."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized or "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise InvalidEmailError("El correo electrónico no es válido.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
