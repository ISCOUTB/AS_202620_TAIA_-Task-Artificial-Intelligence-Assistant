"""Textos fijos que el asistente devuelve sin llamar al modelo de lenguaje.
Solo las dudas del sistema (SYSTEM_HELP) usan el modelo."""

from __future__ import annotations

from datetime import datetime

from backend.app.modules.ai.application.dto import TaskView
from backend.app.modules.ai.domain.messages import ExtractedTaskData


def _when(value: datetime) -> str:
    return value.strftime("%d/%m/%Y %H:%M")


def confirm_create(task: ExtractedTaskData) -> str:
    line = f'Voy a crear la tarea "{task.title}"'
    if task.due_at:
        line += f" para el {_when(task.due_at)}"
    if task.subject:
        line += f" ({task.subject})"
    return line + ". Confirmas? (si / no)"


def confirm_update(title: str, changes: ExtractedTaskData) -> str:
    parts: list[str] = []
    if changes.title:
        parts.append(f'titulo a "{changes.title}"')
    if changes.due_at:
        parts.append(f"entrega al {_when(changes.due_at)}")
    if changes.subject:
        parts.append(f"materia a {changes.subject}")
    detail = ", ".join(parts) if parts else "los datos indicados"
    return f'Voy a cambiar la tarea "{title}": {detail}. Confirmas? (si / no)'


def task_created(task: TaskView) -> str:
    return f'Listo, cree la tarea "{task.title}" para el {_when(task.due_at)}.'


def task_updated(task: TaskView) -> str:
    return f'Listo, actualice la tarea "{task.title}".'


def task_list(tasks: list[TaskView]) -> str:
    if not tasks:
        return "No encontre tareas con esos criterios."
    lines = [f"Tienes {len(tasks)} tarea(s):"]
    for task in tasks:
        lines.append(f'- "{task.title}" ({task.status}) para el {_when(task.due_at)}')
    return "\n".join(lines)


def cancelled() -> str:
    return "Ok, no hago nada."


def not_confirmed() -> str:
    return "No lo tome como un si, asi que cancele. Dime otra vez que necesitas."


def not_understood() -> str:
    return (
        "No entendi bien. Puedo crear, consultar o modificar tareas, "
        "o responder dudas sobre TAIA."
    )


def rephrase() -> str:
    return "No estoy seguro de haber entendido. Puedes decirlo de otra forma?"


def missing_title() -> str:
    return "Para crear la tarea necesito al menos un titulo. Cual seria?"


def missing_due() -> str:
    return "Para crear la tarea necesito una fecha de entrega. Para cuando es?"


def update_target_not_found(hint: str) -> str:
    return f'No encontre una tarea que coincida con "{hint}".'


def update_target_ambiguous(hint: str, count: int) -> str:
    return (
        f'Hay {count} tareas que coinciden con "{hint}". Puedes ser mas especifico?'
    )


def too_long() -> str:
    return "El mensaje es muy largo. Puedes resumirlo?"


def academic_rejected(reason: str) -> str:
    return f"No pude completar la operacion: {reason}"


def service_unavailable() -> str:
    return "Ahora no puedo procesar tu mensaje. Intenta de nuevo en un momento."
