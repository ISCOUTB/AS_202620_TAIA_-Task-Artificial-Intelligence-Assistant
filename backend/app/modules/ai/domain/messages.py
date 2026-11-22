"""Conceptos del dominio de IA: lo que entra, lo que el modelo entiende y lo
que se responde. Nada aqui depende de Gemini, HTTP ni la base de datos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
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

# El contexto expira tras este tiempo sin mensajes (RF-AGT-15).
CONTEXT_TTL = timedelta(minutes=30)

# Debajo de esta confianza no se ofrece confirmacion: se pide reformular.
MIN_CONFIDENCE = 0.6

# Largo maximo de un titulo generado por el modelo (RF-AGT-06).
MAX_GENERATED_TITLE = 60

# Opciones que se muestran cuando hay varias candidatas (RF-AGT-05, 08 y 09).
MAX_OPTIONS = 5

# Elementos que lista una respuesta antes de resumir con "...y N mas" (RF-AGT-11).
MAX_LISTED = 10

# Tipos de actividad (RF-TAR-01), con los valores del diccionario de datos.
TASK_TYPES = ("task", "exam")


class Channel(str, Enum):
    """Medio por el que llega la solicitud."""

    TELEGRAM = "telegram"
    APP = "app"


class Intent(str, Enum):
    """Que quiere hacer el estudiante."""

    CREATE_TASK = "create_task"
    QUERY_TASKS = "query_tasks"
    UPDATE_TASK = "update_task"
    COMPLETE_TASK = "complete_task"
    SUMMARY = "summary"
    QUERY_SCHEDULE = "query_schedule"
    SYSTEM_HELP = "system_help"
    UNKNOWN = "unknown"


class ActionKind(str, Enum):
    """Acciones que requieren confirmacion antes de ejecutarse (RF-AGT-04)."""

    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    COMPLETE_TASK = "complete_task"


@dataclass(frozen=True)
class IncomingRequest:
    """Mensaje del estudiante ya recibido por un adaptador de canal."""

    user_id: str
    text: str
    channel: Channel
    # Mensajes anteriores de la conversacion, del mas antiguo al mas reciente, como
    # pares (rol, texto). Solo sirven de contexto al modelo (RF-AGT-15); nunca
    # llevan identificadores (RF-AGT-17).
    history: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ExtractedTaskData:
    """Datos de una tarea sacados del texto por el modelo. Sin validar: las
    reglas de negocio las aplica el modulo academico."""

    title: str | None = None
    due_at: datetime | None = None
    subject: str | None = None
    description: str | None = None
    # "task" o "exam" (RF-AGT-05); None si el mensaje no lo dice.
    type: str | None = None
    # El modelo genero el titulo porque el mensaje no traia uno (RF-AGT-06).
    title_generated: bool = False


@dataclass(frozen=True)
class ExtractedFilters:
    """Filtros de una consulta de tareas sacados del texto por el modelo."""

    text: str | None = None
    subject: str | None = None
    status: str | None = None
    due_from: datetime | None = None
    due_to: datetime | None = None
    type: str | None = None


@dataclass(frozen=True)
class ExtractedPeriod:
    """Periodo de un resumen o de una consulta del horario, en dias de Colombia.

    `start` y `end` son inclusivos. El backend los convierte en instantes
    (RF-AGT-12, RF-AGT-13); el modelo no hace calculos."""

    start: date
    end: date

    def bounds(self) -> tuple[datetime, datetime]:
        """`[start 00:00, dia siguiente a end 00:00)` en hora de Colombia (RT-03)."""

        start = datetime.combine(self.start, datetime.min.time(), tzinfo=COLOMBIA_TZ)
        end = datetime.combine(self.end + timedelta(days=1), datetime.min.time(), tzinfo=COLOMBIA_TZ)
        return start, end


@dataclass(frozen=True)
class Interpretation:
    """Resultado de interpretar un mensaje con el modelo de lenguaje."""

    intent: Intent
    confidence: float
    task: ExtractedTaskData | None = None
    task_hint: str | None = None
    filters: ExtractedFilters | None = None
    period: ExtractedPeriod | None = None


@dataclass(frozen=True)
class PendingAction:
    """Accion propuesta al estudiante que espera su confirmacion (si / no).

    `task_id` y `subject_id` los resuelve el backend, nunca el modelo (RF-AGT-17)."""

    kind: ActionKind
    task: ExtractedTaskData
    summary: str
    task_id: str | None = None
    task_hint: str | None = None
    subject_id: str | None = None


@dataclass(frozen=True)
class AssistantReply:
    """Respuesta del asistente para el estudiante."""

    text: str
    awaiting_confirmation: bool = False
