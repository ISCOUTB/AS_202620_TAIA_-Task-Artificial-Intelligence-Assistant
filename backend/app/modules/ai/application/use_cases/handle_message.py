"""Caso de uso principal del asistente: recibe un mensaje y decide que hacer.

Flujo: interpretar -> (si escribe: confirmar) -> pedir a academico -> responder.
El modelo de lenguaje piensa; academico valida y persiste. Cada mensaje hace a
lo sumo una llamada al modelo y las respuestas salen de plantillas (RNF-10)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta
import unicodedata

from app.modules.ai.application import replies
from app.modules.ai.application.dto import NewTask, SubjectOption, TaskChanges, TaskFilters
from app.modules.ai.application.ports.academic_gateway import (
    AcademicError,
    AcademicGateway,
    TaskDataRejected,
)
from app.modules.ai.application.ports.conversation_store import ConversationStore
from app.modules.ai.application.ports.llm import LLMError, LLMUsage, LLMPort
from app.modules.ai.domain.conversation import Conversation
from app.modules.ai.domain.messages import (
    COLOMBIA_TZ,
    MAX_INPUT_CHARS,
    MIN_CONFIDENCE,
    ActionKind,
    AssistantReply,
    ExtractedTaskData,
    IncomingRequest,
    Intent,
    Interpretation,
    PendingAction,
)

_YES = {"si", "s", "dale", "ok", "confirmo", "yes", "listo", "hazlo"}
_NO = {"no", "n", "cancela", "cancelar"}

#_Un estudiante escribe "Sí", "SÍ", "¡Sí!" o "sí." tan seguido como "si".
_MARCAS = " \t\n\r.,;:!?¿¡\"'«»()…[]{}–—"


def _normalizar_respuesta(text: str) -> str:
    """Reduce la respuesta a una forma comparable: sin tildes, sin signos, en minusculas.

    Sin esto, "Sí" se convierte en "sí" con `.lower()` y no coincide con _YES,
    que solo contiene "si" sin tilde: la tarea nunca se creaba.
    """

    descompuesto = unicodedata.normalize("NFKD", text)
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return sin_acentos.casefold().strip(_MARCAS)


def _previous_reply(conversation: Conversation) -> str | None:
    """Ultimo mensaje de TAIA, para no repetirlo igual (RF-AGT-22)."""

    for turn in reversed(conversation.turns):
        if turn.role == "assistant":
            return turn.text
    return None


class UsageLimitExceededError(Exception):
    """El estudiante supero el limite de mensajes al asistente (RF-AGT-19)."""


class HandleUserMessageUseCase:
    """Punto de entrada del asistente para un mensaje de un estudiante."""

    def __init__(
        self,
        llm: LLMPort,
        academic: AcademicGateway,
        conversations: ConversationStore,
        now: Callable[[], datetime] | None = None,
        hourly_limit: int = 30,
        daily_limit: int = 200,
    ) -> None:
        self._llm = llm
        self._academic = academic
        self._conversations = conversations
        self._now = now or (lambda: datetime.now(COLOMBIA_TZ))
        # RF-AGT-19: 30 mensajes por hora y 200 por dia, configurables al componer.
        self._hourly_limit = hourly_limit
        self._daily_limit = daily_limit
        self._usage: LLMUsage | None = None

    def last_usage(self) -> LLMUsage | None:
        """Consumo de la llamada al modelo del ultimo mensaje, para medir el costo (S5).

        Es None si ese mensaje no llamo al modelo, como una confirmacion: antes
        se repetia el consumo del mensaje anterior y el costo se contaba doble.
        """

        return self._usage

    def execute(self, request: IncomingRequest) -> AssistantReply:
        self._usage = None
        text = request.text.strip()
        if not text:
            return AssistantReply(replies.rephrase())
        if len(text) > MAX_INPUT_CHARS:
            return AssistantReply(replies.too_long())
        self._check_usage_limit(request.user_id)

        conversation = self._conversations.get(request.user_id)
        conversation.record("user", text)

        reply = self._route(request, text, conversation)

        conversation.record("assistant", reply.text)
        self._conversations.save(conversation)
        return reply

    def _check_usage_limit(self, user_id: str) -> None:
        """Rechaza el mensaje sin llamar al LLM si se supero el limite (RF-AGT-19)."""

        now = self._now()
        windows = (
            (timedelta(hours=1), self._hourly_limit),
            (timedelta(days=1), self._daily_limit),
        )
        for window, limit in windows:
            if self._conversations.count_user_messages_since(user_id, now - window) >= limit:
                raise UsageLimitExceededError(
                    "Alcanzaste el límite de mensajes conmigo por ahora. Inténtalo de nuevo más tarde."
                )

    # -- ruteo ---------------------------------------------------------------

    def _route(
        self, request: IncomingRequest, text: str, conversation: Conversation
    ) -> AssistantReply:
        if conversation.pending is not None:
            action = self._conversations.take_pending(request.user_id)
            conversation.clear_pending()
            if action is not None:
                return self._resolve_pending(request.user_id, text, action)
            # Otra peticion ya la reclamo: se atiende como un mensaje sin
            # accion pendiente, igual que una confirmacion repetida.

        # RF-AGT-15: el modelo recibe los mensajes anteriores para entender
        # continuaciones como "y manana?". El ultimo turno es el mensaje actual.
        history = tuple((turn.role, turn.text) for turn in conversation.turns[:-1])
        try:
            interpretation = self._llm.interpret(replace(request, history=history), self._now())
            self._usage = self._llm.last_usage()
        except LLMError:
            return AssistantReply(replies.service_unavailable())

        intent = interpretation.intent
        if intent is Intent.SYSTEM_HELP:
            return self._system_help(text)
        if intent is Intent.GREETING:
            # RF-AGT-02: respuesta fija con la voz de TAIA, sin otra llamada.
            return AssistantReply(replies.greeting(text, _previous_reply(conversation)))
        handlers = {
            Intent.QUERY_TASKS: self._query_tasks,
            Intent.CREATE_TASK: self._propose_create,
            Intent.UPDATE_TASK: self._propose_update,
            Intent.COMPLETE_TASK: self._propose_complete,
            Intent.SUMMARY: self._summary,
            Intent.QUERY_SCHEDULE: self._schedule,
        }
        handler = handlers.get(intent)
        if handler is None:
            # RF-AGT-02: fuera de la lista cerrada, respuesta fija sin otra llamada.
            return AssistantReply(replies.not_understood(_previous_reply(conversation)))
        try:
            return handler(request.user_id, interpretation, conversation)
        except AcademicError:
            return AssistantReply(replies.service_unavailable())

    # -- lectura (no requiere confirmacion) --------------------------------

    def _system_help(self, question: str) -> AssistantReply:
        try:
            answer = self._llm.answer_system_help(question)
            self._usage = self._llm.last_usage()
        except LLMError:
            return AssistantReply(replies.service_unavailable())
        # RF-AGT-14: una respuesta cortada por el limite de tokens no se muestra.
        if self._usage is not None and self._usage.truncated:
            return AssistantReply(replies.help_truncated())
        return AssistantReply(answer)

    def _query_tasks(
        self, user_id: str, interpretation: Interpretation, _conversation: Conversation
    ) -> AssistantReply:
        found = interpretation.filters
        subject_id = None
        if found and found.subject:
            subject = self._resolve_subject(user_id, found.subject)
            if isinstance(subject, AssistantReply):
                return subject
            subject_id = subject.id
        filters = TaskFilters(
            text=found.text if found else None,
            subject_id=subject_id,
            status=found.status if found else None,
            due_from=found.due_from if found else None,
            due_to=found.due_to if found else None,
            type=found.type if found else None,
        )
        return AssistantReply(replies.task_list(self._academic.list_tasks(user_id, filters)))

    def _summary(
        self, user_id: str, interpretation: Interpretation, _conversation: Conversation
    ) -> AssistantReply:
        """RF-AGT-12: el modelo solo extrae el periodo; academico cuenta."""

        if interpretation.period is None:
            return AssistantReply(replies.missing_summary_period())
        start, end = interpretation.period.bounds()
        summary = self._academic.summarize_period(user_id, start, end)
        return AssistantReply(replies.period_summary(summary))

    def _schedule(
        self, user_id: str, interpretation: Interpretation, _conversation: Conversation
    ) -> AssistantReply:
        """RF-AGT-13: clases del periodo, opcionalmente de una asignatura."""

        if interpretation.period is None:
            return AssistantReply(replies.missing_schedule_period())
        subject_id = None
        found = interpretation.filters
        if found and found.subject:
            subject = self._resolve_subject(user_id, found.subject)
            if isinstance(subject, AssistantReply):
                return subject
            subject_id = subject.id
        start, end = interpretation.period.bounds()
        classes = self._academic.get_classes(user_id, start, end)
        if subject_id is not None:
            classes = [item for item in classes if item.subject_id == subject_id]
        return AssistantReply(replies.class_list(classes))

    def _resolve_subject(self, user_id: str, text: str) -> SubjectOption | AssistantReply:
        """RF-AGT-10: una sola coincidencia da su identificador; si no, se pregunta."""

        options = self._academic.match_subjects(user_id, text)
        if not options:
            return AssistantReply(replies.subject_not_found(text))
        if len(options) > 1:
            return AssistantReply(replies.subject_ambiguous(text, options))
        return options[0]

    # -- escritura (propone y espera confirmacion) ------------------------

    def _propose_create(
        self, user_id: str, interpretation: Interpretation, conversation: Conversation
    ) -> AssistantReply:
        task = interpretation.task or ExtractedTaskData()
        if interpretation.confidence < MIN_CONFIDENCE:
            return AssistantReply(replies.rephrase(_previous_reply(conversation)))
        if not task.title:
            return AssistantReply(replies.missing_title())
        if task.due_at is None:
            return AssistantReply(replies.missing_due())
        if not task.subject:
            return AssistantReply(replies.missing_subject())
        subject = self._resolve_subject(user_id, task.subject)
        if isinstance(subject, AssistantReply):
            return subject

        task = replace(task, subject=subject.name, type=task.type or "task")
        action = PendingAction(
            kind=ActionKind.CREATE_TASK,
            task=task,
            summary=replies.confirm_create(task),
            subject_id=subject.id,
        )
        conversation.set_pending(action)
        return AssistantReply(action.summary, awaiting_confirmation=True)

    def _propose_update(
        self, user_id: str, interpretation: Interpretation, conversation: Conversation
    ) -> AssistantReply:
        changes = interpretation.task or ExtractedTaskData()
        hint = (interpretation.task_hint or "").strip()
        if interpretation.confidence < MIN_CONFIDENCE or _no_changes(changes) or not hint:
            return AssistantReply(replies.rephrase(_previous_reply(conversation)))

        subject_id = None
        if changes.subject:
            subject = self._resolve_subject(user_id, changes.subject)
            if isinstance(subject, AssistantReply):
                return subject
            changes = replace(changes, subject=subject.name)
            subject_id = subject.id

        matches = self._academic.list_tasks(user_id, TaskFilters(text=hint))
        if not matches:
            return AssistantReply(replies.task_not_found(hint))
        if len(matches) > 1:
            return AssistantReply(replies.task_ambiguous(hint, matches))

        target = matches[0]
        action = PendingAction(
            kind=ActionKind.UPDATE_TASK,
            task=changes,
            summary=replies.confirm_update(target.title, changes),
            task_id=target.id,
            task_hint=hint,
            subject_id=subject_id,
        )
        conversation.set_pending(action)
        return AssistantReply(action.summary, awaiting_confirmation=True)

    def _propose_complete(
        self, user_id: str, interpretation: Interpretation, conversation: Conversation
    ) -> AssistantReply:
        """RF-AGT-09: con varias candidatas pendientes no elige, las lista."""

        hint = (interpretation.task_hint or "").strip()
        if interpretation.confidence < MIN_CONFIDENCE or not hint:
            return AssistantReply(replies.rephrase(_previous_reply(conversation)))

        matches = [
            task
            for task in self._academic.list_tasks(user_id, TaskFilters(text=hint))
            if task.status != "completed"
        ]
        if not matches:
            return AssistantReply(replies.task_not_found(hint))
        if len(matches) > 1:
            return AssistantReply(replies.task_ambiguous(hint, matches))

        target = matches[0]
        action = PendingAction(
            kind=ActionKind.COMPLETE_TASK,
            task=ExtractedTaskData(),
            summary=replies.confirm_complete(target),
            task_id=target.id,
            task_hint=hint,
        )
        conversation.set_pending(action)
        return AssistantReply(action.summary, awaiting_confirmation=True)

    # -- confirmacion ----------------------------------------------------

    def _resolve_pending(
        self, user_id: str, text: str, action: PendingAction
    ) -> AssistantReply:
        answer = _normalizar_respuesta(text)

        if answer in _YES:
            return self._execute(user_id, action)
        if answer in _NO:
            return AssistantReply(replies.cancelled())
        return AssistantReply(replies.not_confirmed())

    def _execute(self, user_id: str, action: PendingAction) -> AssistantReply:
        try:
            if action.kind is ActionKind.CREATE_TASK:
                created = self._academic.create_task(user_id, _new_task(action))
                return AssistantReply(replies.task_created(created))
            if action.kind is ActionKind.COMPLETE_TASK:
                completed = self._academic.complete_task(user_id, action.task_id or "")
                return AssistantReply(replies.task_completed(completed))

            updated = self._academic.update_task(
                user_id, action.task_id or "", _task_changes(action)
            )
            return AssistantReply(replies.task_updated(updated))
        except TaskDataRejected as error:
            return AssistantReply(replies.academic_rejected(str(error)))
        except AcademicError:
            return AssistantReply(replies.service_unavailable())


def _new_task(action: PendingAction) -> NewTask:
    data = action.task
    # due_at ya viene garantizado por _propose_create.
    return NewTask(
        title=data.title or "",
        due_at=data.due_at,  # type: ignore[arg-type]
        subject=data.subject,
        description=data.description,
        subject_id=action.subject_id,
        type=data.type or "task",
    )


def _task_changes(action: PendingAction) -> TaskChanges:
    data = action.task
    return TaskChanges(
        title=data.title,
        due_at=data.due_at,
        subject=data.subject,
        description=data.description,
        subject_id=action.subject_id,
    )


def _no_changes(data: ExtractedTaskData) -> bool:
    return not any((data.title, data.due_at, data.subject, data.description))
