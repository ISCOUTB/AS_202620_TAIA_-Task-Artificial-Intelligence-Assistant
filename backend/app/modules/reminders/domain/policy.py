"""Política de recordatorios por defecto (RF-REC-02)."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from app.shared.clock import BOGOTA_TZ, as_bogota

REMINDER_HOUR = time(18, 0)
WINDOW_DAYS = 14
FALLBACK_BEFORE_DUE = timedelta(minutes=60)


def default_schedule(due_at: datetime, now: datetime) -> list[datetime]:
    """Horas de los recordatorios automáticos de una actividad, en orden.

    La tarde anterior (D-1) y cada 2 días hacia atrás (D-2, D-4… hasta D-14), a las
    18:00 de Colombia, solo las futuras. Si ninguna queda en el futuro y faltan más
    de 60 minutos para `due_at`, una sola 60 minutos antes.
    """

    due = as_bogota(due_at)
    now = as_bogota(now)
    days_before = [1, *range(2, WINDOW_DAYS + 1, 2)]
    candidates = sorted(
        datetime.combine(due.date() - timedelta(days=days), REMINDER_HOUR, tzinfo=BOGOTA_TZ)
        for days in days_before
    )
    future = [moment for moment in candidates if moment > now]
    if future:
        return future
    fallback = due - FALLBACK_BEFORE_DUE
    return [fallback] if fallback > now else []
