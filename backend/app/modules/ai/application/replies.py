"""Textos fijos que el asistente devuelve sin llamar al modelo de lenguaje.
Solo las dudas del sistema (SYSTEM_HELP) usan el modelo (RNF-10)."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.modules.ai.application.dto import ClassView, PeriodSummary, SubjectOption, TaskView
from app.modules.ai.domain.messages import (
    COLOMBIA_TZ,
    MAX_LISTED,
    MAX_OPTIONS,
    ExtractedTaskData,
)

_PRIORITY = {"high": "alta", "medium": "media", "low": "baja"}
_STATUS = {"completed": "completada", "overdue": "vencida"}
_WEEKDAYS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
# RF-AGT-07: lo que aplica Academic al crear sin indicar recordatorios (RF-REC-02).
_DEFAULT_REMINDERS = "con recordatorios cada 2 dias y la tarde anterior"


def _local(value: datetime) -> datetime:
    """Toda fecha se muestra en hora de Colombia (RT-03)."""

    return value.astimezone(COLOMBIA_TZ) if value.tzinfo else value


def _when(value: datetime) -> str:
    return _local(value).strftime("%d/%m/%Y %H:%M")


def _day(value: datetime) -> str:
    local = _local(value)
    return f"{_WEEKDAYS[local.weekday()]} {local.strftime('%d/%m/%Y')}"


def _kind(task_type: str | None) -> str:
    return "el examen" if task_type == "exam" else "la tarea"


def _more(total: int, shown: int) -> list[str]:
    return [f"...y {total - shown} mas."] if total > shown else []


# -- crear, actualizar y completar ---------------------------------------


def confirm_create(task: ExtractedTaskData) -> str:
    """Resumen de RF-AGT-04 con el titulo (tambien el generado, RF-AGT-06) y los
    recordatorios por defecto (RF-AGT-07)."""

    line = f'Voy a crear {_kind(task.type)} "{task.title}"'
    if task.subject:
        line += f" de {task.subject}"
    if task.due_at:
        line += f" para el {_when(task.due_at)}"
    return line + f", {_DEFAULT_REMINDERS}. Confirmas? (si / no)"


def confirm_update(title: str, changes: ExtractedTaskData) -> str:
    parts: list[str] = []
    if changes.title:
        parts.append(f'titulo a "{changes.title}"')
    if changes.due_at:
        parts.append(f"entrega al {_when(changes.due_at)}")
    if changes.subject:
        parts.append(f"asignatura a {changes.subject}")
    if changes.description:
        parts.append("descripcion")
    detail = ", ".join(parts) if parts else "los datos indicados"
    return f'Voy a cambiar la tarea "{title}": {detail}. Confirmas? (si / no)'


def confirm_complete(task: TaskView) -> str:
    return (
        f'Voy a marcar como completada {_kind(task.type)} "{task.title}"'
        f"{_of_subject(task)}. Confirmas? (si / no)"
    )


def task_created(task: TaskView) -> str:
    return f'Listo, cree {_kind(task.type)} "{task.title}" para el {_when(task.due_at)}.'


def task_updated(task: TaskView) -> str:
    return f'Listo, actualice la tarea "{task.title}".'


def task_completed(task: TaskView) -> str:
    return f'Listo, marque como completada {_kind(task.type)} "{task.title}".'


def _of_subject(task: TaskView) -> str:
    return f" ({task.subject})" if task.subject else ""


# -- asignatura (RF-AGT-05 y RF-AGT-10) -----------------------------------


def missing_subject() -> str:
    return (
        "De que asignatura es? Escribe de nuevo la solicitud indicando la asignatura."
    )


def subject_not_found(text: str) -> str:
    return (
        f'No encontre la asignatura "{text}" entre las tuyas. Registrala en la '
        "aplicacion o escribe de nuevo la solicitud con otro nombre."
    )


def subject_ambiguous(text: str, options: list[SubjectOption]) -> str:
    names = ", ".join(option.name for option in options[:MAX_OPTIONS])
    return (
        f'Varias asignaturas coinciden con "{text}": {names}. Escribe de nuevo la '
        "solicitud con el nombre de la asignatura."
    )


# -- consultas (RF-AGT-11, 12 y 13) ---------------------------------------


def _task_line(task: TaskView) -> str:
    line = f'- "{task.title}"{_of_subject(task)} para el {_when(task.due_at)}'
    if task.status in _STATUS:
        return f"{line}, {_STATUS[task.status]}"
    if task.priority in _PRIORITY:
        return f"{line}, prioridad {_PRIORITY[task.priority]}"
    return line


def task_list(tasks: list[TaskView]) -> str:
    """Hasta 10 actividades por fecha limite, con su prioridad (RF-AGT-11)."""

    if not tasks:
        return "No encontre tareas con esos criterios."
    ordered = sorted(tasks, key=lambda task: task.due_at)
    lines = [f"Tienes {len(tasks)} actividad(es):"]
    lines += [_task_line(task) for task in ordered[:MAX_LISTED]]
    lines += _more(len(tasks), MAX_LISTED)
    return "\n".join(lines)


def period_summary(summary: PeriodSummary) -> str:
    """Conteos calculados por el backend (RF-AGT-12); el modelo no hace calculos."""

    last_day = summary.end - timedelta(microseconds=1)
    lines = [
        f"Resumen del {_local(summary.start).strftime('%d/%m/%Y')} al "
        f"{_local(last_day).strftime('%d/%m/%Y')}: {summary.pending} pendiente(s), "
        f"{summary.completed} completada(s) y {summary.overdue} vencida(s)."
    ]
    lines += [
        f"- {item.name}: {item.pending} pendiente(s), {item.completed} completada(s), "
        f"{item.overdue} vencida(s)"
        for item in summary.by_subject
    ]
    if summary.next_due is not None:
        task = summary.next_due
        lines.append(f'Proxima por vencer: "{task.title}"{_of_subject(task)} el {_when(task.due_at)}.')
    return "\n".join(lines)


def class_list(classes: list[ClassView]) -> str:
    """Clases del periodo, por inicio (RF-AGT-13)."""

    if not classes:
        return "No tienes clases registradas en ese periodo."
    lines = [f"Tienes {len(classes)} clase(s):"]
    for item in classes[:MAX_LISTED]:
        room = f", salon {item.room}" if item.room else ""
        lines.append(
            f"- {_day(item.starts_at)} {_local(item.starts_at).strftime('%H:%M')}-"
            f"{_local(item.ends_at).strftime('%H:%M')} {item.subject_name}{room}"
        )
    lines += _more(len(classes), MAX_LISTED)
    return "\n".join(lines)


def missing_summary_period() -> str:
    return "De que periodo quieres el resumen? Por ejemplo: este mes o esta semana."


def missing_schedule_period() -> str:
    return "De que dia quieres ver tus clases? Por ejemplo: hoy, manana o el jueves."


# -- confirmacion y errores ------------------------------------------------


def cancelled() -> str:
    return "Ok, no hago nada."


def not_confirmed() -> str:
    return "No lo tome como un si, asi que cancele. Dime otra vez que necesitas."


def not_understood() -> str:
    """Respuesta fija para lo que no esta en la lista cerrada (RF-AGT-02)."""

    return (
        "No entendi bien. Puedo crear, consultar, modificar o completar tareas y "
        "examenes, darte un resumen de un periodo, mostrarte tu horario o responder "
        "dudas sobre TAIA."
    )


def rephrase() -> str:
    return "No estoy seguro de haber entendido. Puedes decirlo de otra forma?"


def missing_title() -> str:
    return "Para crear la tarea necesito al menos un titulo. Cual seria?"


def missing_due() -> str:
    return "Para crear la tarea necesito una fecha de entrega. Para cuando es?"


def task_not_found(hint: str) -> str:
    return f'No encontre una tarea que coincida con "{hint}".'


def task_ambiguous(hint: str, tasks: list[TaskView]) -> str:
    """Lista hasta 5 candidatas y no elige (RF-AGT-08, RF-AGT-09)."""

    lines = [f'Hay {len(tasks)} tareas que coinciden con "{hint}":']
    lines += [
        f'- "{task.title}"{_of_subject(task)} para el {_when(task.due_at)}'
        for task in sorted(tasks, key=lambda task: task.due_at)[:MAX_OPTIONS]
    ]
    lines.append("Puedes ser mas especifico?")
    return "\n".join(lines)


def too_long() -> str:
    return "El mensaje es muy largo. Puedes resumirlo?"


def academic_rejected(reason: str) -> str:
    return f"No pude completar la operacion: {reason}"


def help_truncated() -> str:
    """RF-AGT-14: una respuesta cortada por el limite de tokens no se muestra."""

    return "No pude armar una respuesta corta a esa duda. Puedes preguntarla de forma mas concreta?"


def service_unavailable() -> str:
    return "Ahora no puedo procesar tu mensaje. Intenta de nuevo en un momento."
