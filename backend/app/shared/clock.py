"""Hora oficial del sistema (RT-03).

Toda fecha que ve o escribe el usuario está en hora de Colombia. Colombia no
tiene horario de verano, así que un desplazamiento fijo es correcto y evita
depender de tzdata.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone

BOGOTA_TZ = timezone(timedelta(hours=-5), "America/Bogota")

Clock = Callable[[], datetime]


def now_bogota() -> datetime:
    """Momento actual con zona America/Bogota. Nunca usa la hora local del servidor."""

    return datetime.now(BOGOTA_TZ)


def as_bogota(value: datetime) -> datetime:
    """Interpreta una fecha sin zona como hora de Colombia y convierte las que tienen zona."""

    if value.tzinfo is None:
        return value.replace(tzinfo=BOGOTA_TZ)
    return value.astimezone(BOGOTA_TZ)


def end_of_day_bogota(value: date) -> datetime:
    """Una fecha sin hora se interpreta como las 23:59 de ese día en Colombia (RT-03)."""

    return datetime.combine(value, time(23, 59), tzinfo=BOGOTA_TZ)
