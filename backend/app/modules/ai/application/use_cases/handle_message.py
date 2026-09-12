"""Caso de uso principal del asistente: recibe un mensaje y decide que hacer.

Flujo: interpretar -> (si escribe: confirmar) -> pedir a academico -> responder.
El modelo de lenguaje piensa; academico valida y persiste."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from backend.app.modules.ai.application import replies
from backend.app.modules.ai.application.dto import NewTask, TaskChanges, TaskFilters
from backend.app.modules.ai.application.ports.academic_gateway import (
    AcademicError,
    AcademicGateway,
    TaskDataRejected,
)
from backend.app.modules.ai.application.ports.conversation_store import ConversationStore
from backend.app.modules.ai.application.ports.llm import LLMError, LLMPort
from backend.app.modules.ai.domain.conversation import Conversation
from backend.app.modules.ai.domain.messages import (
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


class HandleUserMessageUseCase:
    """Punto de entrada del asistente para un mensaje de un estudiante."""

    def __init__(
        self,
        llm: LLMPort,
        academic: AcademicGateway,
        conversations: ConversationStore,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._llm = llm
        self._academic = academic
        self._conversations = conversations
        self._now = now or (lambda: datetime.now(COLOMBIA_TZ))

    def execute(self, request: IncomingRequest) -> AssistantReply:
        text = request.text.strip()
        if not text:
            return AssistantReply(replies.rephrase())
        if len(text) > MAX_INPUT_CHARS:
            return AssistantReply(replies.too_long())

        conversation = self._conversations.get(request.user_id)
        conversation.record("user", text)

        reply = self._route(request, text, conversation)

        conversation.record("assistant", reply.text)
        self._conversations.save(conversation)
        return reply

    # -- ruteo ---------------------------------------------------------------

    def _route(
        self, request: IncomingRequest, text: str, conversation: Conversation
    ) -> AssistantReply:
        if conversation.pending is not None:
            return self._resolve_pending(request.user_id, text, conversation)

        try:
            interpretation = self._llm.interpret(request, self._now())
        except LLMError:
            return AssistantReply(replies.service_unavailable())

        intent = interpretation.intent
        if intent is Intent.SYSTEM_HELP:
            return self._system_help(text)
        if intent is Intent.QUERY_TASKS:
            return self._query_tasks(request.user_id, interpretation)
        if intent is Intent.CREATE_TASK:
            return self._propose_create(interpretation, conversation)
        if intent is Intent.UPDATE_TASK:
            return self._propose_update(request.user_id, interpretation, conversation)
        return AssistantReply(replies.not_understood())

    # -- lectura (no requiere confirmacion) --------------------------------

    def _system_help(self, question: str) -> AssistantReply:
        try:
            return AssistantReply(self._llm.answer_system_help(question))
        except LLMError:
            return AssistantReply(replies.service_unavailable())

    def _query_tasks(
        self, user_id: str, interpretation: Interpretation
    ) -> AssistantReply:
        found = interpretation.filters
        filters = TaskFilters(
            text=found.text if found else None,
            subject=found.subject if found else None,
            status=found.status if found else None,
            due_from=found.due_from if found else None,
            due_to=found.due_to if found else None,
        )
        try:
            tasks = self._academic.list_tasks(user_id, filters)
        except AcademicError:
            return AssistantReply(replies.service_unavailable())
        return AssistantReply(replies.task_list(tasks))

    # -- escritura (propone y espera confirmacion) ------------------------

    def _propose_create(
        self, interpretation: Interpretation, conversation: Conversation
    ) -> AssistantReply:
        task = interpretation.task or ExtractedTaskData()
        if interpretation.confidence < MIN_CONFIDENCE:
            return AssistantReply(replies.rephrase())
        if not task.title:
            return AssistantReply(replies.missing_title())
        if task.due_at is None:
            return AssistantReply(replies.missing_due())

        action = PendingAction(
            kind=ActionKind.CREATE_TASK,
            task=task,
            summary=replies.confirm_create(task),
        )
        conversation.set_pending(action)
        return AssistantReply(action.summary, awaiting_confirmation=True)

    def _propose_update(
        self, user_id: str, interpretation: Interpretation, conversation: Conversation
    ) -> AssistantReply:
        changes = interpretation.task or ExtractedTaskData()
        hint = (interpretation.task_hint or "").strip()
        if _no_changes(changes) or not hint:
            return AssistantReply(replies.rephrase())

        try:
            matches = self._academic.list_tasks(user_id, TaskFilters(text=hint))
        except AcademicError:
            return AssistantReply(replies.service_unavailable())

        if not matches:
            return AssistantReply(replies.update_target_not_found(hint))
        if len(matches) > 1:
            return AssistantReply(replies.update_target_ambiguous(hint, len(matches)))

        target = matches[0]
        action = PendingAction(
            kind=ActionKind.UPDATE_TASK,
            task=changes,
            summary=replies.confirm_update(target.title, changes),
            task_id=target.id,
            task_hint=hint,
        )
        conversation.set_pending(action)
        return AssistantReply(action.summary, awaiting_confirmation=True)

    # -- confirmacion ----------------------------------------------------

    def _resolve_pending(
        self, user_id: str, text: str, conversation: Conversation
    ) -> AssistantReply:
        answer = text.lower().strip(" .!?")
        action = conversation.pending
        conversation.clear_pending()

        if answer in _YES:
            return self._execute(user_id, action)
        if answer in _NO:
            return AssistantReply(replies.cancelled())
        return AssistantReply(replies.not_confirmed())

    def _execute(self, user_id: str, action: PendingAction) -> AssistantReply:
        try:
            if action.kind is ActionKind.CREATE_TASK:
                created = self._academic.create_task(user_id, _new_task(action.task))
                return AssistantReply(replies.task_created(created))

            updated = self._academic.update_task(
                user_id, action.task_id or "", _task_changes(action.task)
            )
            return AssistantReply(replies.task_updated(updated))
        except TaskDataRejected as error:
            return AssistantReply(replies.academic_rejected(str(error)))
        except AcademicError:
            return AssistantReply(replies.service_unavailable())


def _new_task(data: ExtractedTaskData) -> NewTask:
    # due_at ya viene garantizado por _propose_create.
    return NewTask(
        title=data.title or "",
        due_at=data.due_at,  # type: ignore[arg-type]
        subject=data.subject,
        description=data.description,
    )


def _task_changes(data: ExtractedTaskData) -> TaskChanges:
    return TaskChanges(
        title=data.title,
        due_at=data.due_at,
        subject=data.subject,
        description=data.description,
    )


def _no_changes(data: ExtractedTaskData) -> bool:
    return not any((data.title, data.due_at, data.subject, data.description))
