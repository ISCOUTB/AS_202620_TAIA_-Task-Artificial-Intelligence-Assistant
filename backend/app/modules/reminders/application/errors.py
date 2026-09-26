"""Errores de aplicación del módulo Reminders."""


class ReminderNotFoundError(ValueError):
    """El recordatorio no existe o no pertenece al usuario (RT-02)."""
