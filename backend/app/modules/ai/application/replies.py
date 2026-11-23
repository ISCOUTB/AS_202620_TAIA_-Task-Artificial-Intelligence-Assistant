"""Textos fijos que TAIA devuelve sin llamar al modelo de lenguaje.
Solo las dudas del sistema (SYSTEM_HELP) usan el modelo (RNF-10).

Todos siguen la voz de TAIA (RF-AGT-22): primera persona, en femenino, con
tildes y como maximo un emoji, que se escribe como secuencia de escape."""

from __future__ import annotations

from datetime import datetime, timedelta
import unicodedata

from app.modules.ai.application.dto import ClassView, PeriodSummary, SubjectOption, TaskView
from app.modules.ai.domain.messages import (
    COLOMBIA_TZ,
    MAX_LISTED,
    MAX_OPTIONS,
    ExtractedTaskData,
)

OCTOPUS = "\U0001F419"
PARTY = "\U0001F389"

_PRIORITY = {"high": "alta", "medium": "media", "low": "baja"}
_STATUS = {"completed": "completada", "overdue": "vencida"}
_WEEKDAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
# RF-AGT-07: lo que aplica Academic al crear sin indicar recordatorios (RF-REC-02).
_DEFAULT_REMINDERS = "con recordatorios cada 2 días y la tarde anterior"
_CONFIRM = "¿Lo confirmo? (sí / no)"


def _vary(variants: tuple[str, ...], previous: str | None) -> str:
    """RF-AGT-22: si la respuesta repetiría el mensaje anterior de TAIA, se usa otra."""

    for variant in variants:
        if variant != previous:
            return variant
    return variants[0]


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
    return [f"...y {total - shown} más."] if total > shown else []


# -- crear, actualizar y completar ---------------------------------------


def confirm_create(task: ExtractedTaskData) -> str:
    """Resumen de RF-AGT-04 con el título (también el generado, RF-AGT-06) y los
    recordatorios por defecto (RF-AGT-07). Sin emoji: pide confirmar una escritura."""

    line = f'Voy a crear {_kind(task.type)} "{task.title}"'
    if task.subject:
        line += f" de {task.subject}"
    if task.due_at:
        line += f" para el {_when(task.due_at)}"
    return line + f", {_DEFAULT_REMINDERS}. {_CONFIRM}"


def confirm_update(title: str, changes: ExtractedTaskData) -> str:
    parts: list[str] = []
    if changes.title:
        parts.append(f'título a "{changes.title}"')
    if changes.due_at:
        parts.append(f"entrega al {_when(changes.due_at)}")
    if changes.subject:
        parts.append(f"asignatura a {changes.subject}")
    if changes.description:
        parts.append("descripción")
    detail = ", ".join(parts) if parts else "los datos indicados"
    return f'Voy a cambiar la tarea "{title}": {detail}. {_CONFIRM}'


def confirm_complete(task: TaskView) -> str:
    return (
        f'Voy a marcar como completada {_kind(task.type)} "{task.title}"'
        f"{_of_subject(task)}. {_CONFIRM}"
    )


def task_created(task: TaskView) -> str:
    return (
        f'¡Listo! Ya creé {_kind(task.type)} "{task.title}" para el {_when(task.due_at)}. '
        "Yo te aviso antes de que se venza."
    )


def task_updated(task: TaskView) -> str:
    return f'¡Hecho! Actualicé la tarea "{task.title}".'


def task_completed(task: TaskView) -> str:
    return f'¡Bien hecho! Marqué como completada {_kind(task.type)} "{task.title}" {PARTY}'


def _of_subject(task: TaskView) -> str:
    return f" ({task.subject})" if task.subject else ""


# -- asignatura (RF-AGT-05 y RF-AGT-10) -----------------------------------


def missing_subject() -> str:
    return "¿De qué asignatura es? Escríbeme de nuevo la solicitud con la asignatura."


def subject_not_found(text: str) -> str:
    return (
        f'No encontré la asignatura "{text}" entre las tuyas. Regístrala en la '
        "app o escríbeme de nuevo con otro nombre."
    )


def subject_ambiguous(text: str, options: list[SubjectOption]) -> str:
    names = ", ".join(option.name for option in options[:MAX_OPTIONS])
    return (
        f'Varias de tus asignaturas coinciden con "{text}": {names}. Escríbeme de '
        "nuevo con el nombre de la asignatura."
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
    """Hasta 10 actividades por fecha límite, con su prioridad (RF-AGT-11)."""

    if not tasks:
        return "No encontré actividades con esos criterios."
    ordered = sorted(tasks, key=lambda task: task.due_at)
    lines = [f"Tienes {len(tasks)} actividad(es):"]
    lines += [_task_line(task) for task in ordered[:MAX_LISTED]]
    lines += _more(len(tasks), MAX_LISTED)
    return "\n".join(lines)


def period_summary(summary: PeriodSummary) -> str:
    """Conteos calculados por el backend (RF-AGT-12); el modelo no hace cálculos."""

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
        lines.append(f'Próxima por vencer: "{task.title}"{_of_subject(task)} el {_when(task.due_at)}.')
    return "\n".join(lines)


def class_list(classes: list[ClassView]) -> str:
    """Clases del período, por inicio (RF-AGT-13)."""

    if not classes:
        return "No tienes clases registradas en ese período."
    lines = [f"Tienes {len(classes)} clase(s):"]
    for item in classes[:MAX_LISTED]:
        room = f", salón {item.room}" if item.room else ""
        lines.append(
            f"- {_day(item.starts_at)} {_local(item.starts_at).strftime('%H:%M')}-"
            f"{_local(item.ends_at).strftime('%H:%M')} {item.subject_name}{room}"
        )
    lines += _more(len(classes), MAX_LISTED)
    return "\n".join(lines)


def missing_summary_period() -> str:
    return "De qué período quieres el resumen? Por ejemplo: este mes o esta semana."


def missing_schedule_period() -> str:
    return "¿De qué día quieres ver tus clases? Por ejemplo: hoy, mañana o el jueves."


# -- confirmacion y errores ------------------------------------------------


def cancelled() -> str:
    return "Listo, no hago nada."


def not_confirmed() -> str:
    return "No lo tomé como un sí, así que lo cancelé. ¿Qué necesitas?"


_NOT_UNDERSTOOD = (
    "Mmm, no te entendí bien. Puedo crear, consultar, cambiar o completar tus tareas y "
    "exámenes, darte un resumen de un período, decirte tu horario o resolver tus dudas "
    "sobre mí. ¿Con qué te ayudo?",
    "Eso todavía no lo sé hacer. Pídeme que cree, busque, cambie o complete una "
    "actividad, que te haga un resumen o que te diga tu horario.",
    'Creo que no te estoy entendiendo??? Prueba con algo como "tengo parcial de '
    'cálculo el viernes" o "¿qué tengo esta semana?".',
)

_REPHRASE = (
    "No estoy segura de haberte entendido. Me lo dices de otra forma?",
    "Perdón, se me escapó. ¿Me lo repites con otras palabras?",
)


def not_understood(previous: str | None = None) -> str:
    """Respuesta fija para lo que no está en la lista cerrada (RF-AGT-02, RF-AGT-22)."""

    return _vary(_NOT_UNDERSTOOD, previous)


def rephrase(previous: str | None = None) -> str:
    return _vary(_REPHRASE, previous)


_THANKS_WORDS = ("gracias", "agradezco", "thank")
_BYE_WORDS = ("chao", "adiós", "hasta luego", "hasta mañana", "nos vemos", "bye", "buenas noches")

_HELLO = (
    f"¡Hola! Soy TAIA, tu compañera de estudio {OCTOPUS} Puedo crear, consultar, "
    "cambiar o completar tus tareas y exámenes, darte un resumen o decirte tu horario. "
    "¿Qué hacemos hoy?",
    "¡Hola de nuevo! Cuéntame qué necesitas: una tarea nueva, tus pendientes o tu horario?",
)
_THANKS = (
    f"¡Con gusto! Aquí estoy cuando me necesites {OCTOPUS}",
    "¡De nada! Para eso estoy.",
)
_ACK_WORDS = ("ok", "okay", "okey", "vale", "dale", "perfecto", "listo", "bueno", "entendido")

_ACK = (
    f"¡Listo! Si necesitas algo, aquí estoy {OCTOPUS}",
    "¡Perfecto! Cuando quieras seguimos.",
)
_BYE = (
    f"¡Chao! Mucho éxito con tus clases {OCTOPUS}",
    "¡Nos vemos! Aquí te espero cuando quieras.",
)


def _plain(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in folded if not unicodedata.combining(c))


def greeting(text: str, previous: str | None = None) -> str:
    """Saludo, agradecimiento, despedida o acuse corto (RF-AGT-02, intención `greeting`).

    El modelo solo dice que es un saludo; el tipo se decide aquí con palabras
    clave, sin otra llamada al modelo.
    """

    plain = _plain(text)
    if any(_plain(word) in plain for word in _THANKS_WORDS):
        return _vary(_THANKS, previous)
    if any(_plain(word) in plain for word in _BYE_WORDS):
        return _vary(_BYE, previous)
    words = "".join(c if c.isalnum() else " " for c in plain).split()
    # Un acuse corto ("ok", "vale") o solo emojis y signos, sin letras.
    if not words or all(word in _ACK_WORDS for word in words):
        return _vary(_ACK, previous)
    return _vary(_HELLO, previous)


def missing_title() -> str:
    return "Para crear la tarea necesito al menos un título. ¿Cuál sería?"


def missing_due() -> str:
    return "Para crear la tarea necesito la fecha de entrega. Para cuándo es?"


def task_not_found(hint: str) -> str:
    return f'No encontré una tarea que coincida con "{hint}".'


def task_ambiguous(hint: str, tasks: list[TaskView]) -> str:
    """Lista hasta 5 candidatas y no elige (RF-AGT-08, RF-AGT-09)."""

    lines = [f'Hay {len(tasks)} tareas que coinciden con "{hint}":']
    lines += [
        f'- "{task.title}"{_of_subject(task)} para el {_when(task.due_at)}'
        for task in sorted(tasks, key=lambda task: task.due_at)[:MAX_OPTIONS]
    ]
    lines.append("¿Me dices cuál?")
    return "\n".join(lines)


def too_long() -> str:
    return "Uy, ese mensaje es muy largo. ¿Me lo resumes?"


def academic_rejected(reason: str) -> str:
    return f"No pude completar la operación: {reason}"


def help_truncated() -> str:
    """RF-AGT-14: una respuesta cortada por el límite de tokens no se muestra."""

    return "No logré armar una respuesta corta a esa duda. ¿Me la preguntas de forma más concreta?"


def service_unavailable() -> str:
    return "Ahora mismo no puedo procesar tu mensaje. Inténtalo de nuevo en un momento."
