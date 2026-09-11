"""Conceptos del dominio de IA: lo que entra, lo que el modelo entiende y lo
que se responde. Nada aqui depende de Gemini, HTTP ni la base de datos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

# Hora local del estudiante. Colombia no tiene horario de verano, asi que un
# offset fijo es correcto y evita depender de zoneinfo/tzdata.
COLOMBIA_TZ = timezone(timedelta(hours=-5), "America/Bogota")

# Texto maximo aceptado del usuario; evita prompts enormes y gasto de tokens.
MAX_INPUT_CHARS = 1000

# Mensajes que recuerda la conversacion (usuario + asistente).
HISTORY_LIMIT = 10

# Tamano aproximado de esa memoria, como proxy de tokens (sin tokenizador).
MAX_HISTORY_CHARS = 4000

# Debajo de esta confianza no se ofrece confirmacion: se pide reformular.
MIN_CONFIDENCE = 0.6


class Channel(str, Enum):
    """Medio por el que llega la solicitud."""

    TELEGRAM = "telegram"
    APP = "app"


class Intent(str, Enum):
    """Que quiere hacer el estudiante."""

    CREATE_TASK = "create_task"
    QUERY_TASKS = "query_tasks"
    UPDATE_TASK = "update_task"
    SYSTEM_HELP = "system_help"
    UNKNOWN = "unknown"


class ActionKind(str, Enum):
    """Acciones que requieren confirmacion antes de ejecutarse."""

    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"


@dataclass(frozen=True)
class IncomingRequest:
    """Mensaje del estudiante ya recibido por un adaptador de canal."""

    user_id: str
    text: str
    channel: Channel


@dataclass(frozen=True)
class ExtractedTaskData:
    """Datos de una tarea sacados del texto por el modelo. Sin validar: las
    reglas de negocio las aplica el modulo academico."""

    title: str | None = None
    due_at: datetime | None = None
    subject: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class ExtractedFilters:
    """Filtros de una consulta de tareas sacados del texto por el modelo."""

    text: str | None = None
    subject: str | None = None
    status: str | None = None
    due_from: datetime | None = None
    due_to: datetime | None = None


@dataclass(frozen=True)
class Interpretation:
    """Resultado de interpretar un mensaje con el modelo de lenguaje."""

    intent: Intent
    confidence: float
    task: ExtractedTaskData | None = None
    task_hint: str | None = None
    filters: ExtractedFilters | None = None


@dataclass(frozen=True)
class PendingAction:
    """Accion propuesta al estudiante que espera su confirmacion (si / no)."""

    kind: ActionKind
    task: ExtractedTaskData
    summary: str
    task_id: str | None = None
    task_hint: str | None = None


@dataclass(frozen=True)
class AssistantReply:
    """Respuesta del asistente para el estudiante."""

    text: str
    awaiting_confirmation: bool = False
