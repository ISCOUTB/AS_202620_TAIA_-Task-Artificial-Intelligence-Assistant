"""Errores de aplicación del módulo Reminders.

Todos heredan de `ValueError`, como los de Academic, para que un llamador de otro
módulo pueda tratarlos como datos inválidos. El adaptador HTTP los distingue por
su tipo, nunca por el texto (RT-05).
"""


class ReminderNotFoundError(ValueError):
    """El recordatorio no existe o no pertenece al usuario (RT-02): `404`."""


class ReminderTaskNotFoundError(ValueError):
    """La actividad no existe, está eliminada o es de otro usuario (RT-02): `404`."""


class NotificationNotFoundError(ValueError):
    """La notificación no existe o no pertenece al usuario (RT-02): `404`."""


class InvalidReminderError(ValueError):
    """La fecha o el mensaje violan RF-REC-01: `422`."""


class ReminderStateError(ValueError):
    """El estado del recordatorio o de la actividad no permite la operación: `409`."""
