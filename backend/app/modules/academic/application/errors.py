"""Errores de aplicación del módulo Academic para asignaturas, horario y período."""


class SubjectNotFoundError(ValueError):
    """La asignatura no existe o no pertenece al usuario (RT-02)."""


class SubjectAlreadyExistsError(ValueError):
    """El usuario ya tiene una asignatura con ese nombre normalizado."""


class SubjectArchivedError(ValueError):
    """La operación requiere una asignatura activa."""


class ScheduleBlockNotFoundError(ValueError):
    """El bloque no existe o no pertenece al usuario (RT-02)."""


class ScheduleOverlapError(ValueError):
    """El bloque se solapa con otro bloque del mismo usuario."""


class AliasNotFoundError(ValueError):
    """El alias no existe en la asignatura."""


class AcademicPeriodNotFoundError(ValueError):
    """El usuario no ha definido un período académico."""


class SubjectHasTasksError(ValueError):
    """La asignatura tiene actividades asociadas y solo puede archivarse (RF-ASG-04)."""


class TaskNotFoundError(ValueError):
    """La tarea no existe, fue eliminada o no pertenece al usuario (RT-02)."""
