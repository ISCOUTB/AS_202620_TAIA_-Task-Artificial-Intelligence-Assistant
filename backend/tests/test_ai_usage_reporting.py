"""Consumo del modelo por mensaje (S5): solo se informa si el mensaje llamó al modelo."""

from datetime import datetime, timedelta, timezone

from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import InMemoryAcademicGateway
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.application.ports.llm import LLMUsage
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.domain.messages import (
    Channel,
    ExtractedTaskData,
    IncomingRequest,
    Intent,
    Interpretation,
)

DUE = datetime.now(timezone(timedelta(hours=-5))) + timedelta(days=3)


class _ReportingLLM(FakeLLM):
    """Doble que informa consumo, como Gemini y Groq."""

    def last_usage(self):
        return LLMUsage(model="modelo", prompt_tokens=700, candidates_tokens=150, total_tokens=850)


def _msg(text: str) -> IncomingRequest:
    return IncomingRequest(user_id="u1", text=text, channel=Channel.APP)


def _use_case() -> HandleUserMessageUseCase:
    llm = _ReportingLLM(
        [
            Interpretation(
                intent=Intent.CREATE_TASK,
                confidence=0.95,
                task=ExtractedTaskData(title="Taller", due_at=DUE, subject="Redes"),
            )
        ]
    )
    return HandleUserMessageUseCase(
        llm=llm,
        academic=InMemoryAcademicGateway(),
        conversations=InMemoryConversationStore(),
    )


def test_message_that_calls_the_model_reports_its_usage():
    use_case = _use_case()

    use_case.execute(_msg("crea la tarea Taller"))

    assert use_case.last_usage().total_tokens == 850


def test_confirmation_does_not_repeat_the_previous_usage():
    """La confirmación no llama al modelo: antes se registraba otra vez el consumo anterior."""
    use_case = _use_case()
    use_case.execute(_msg("crea la tarea Taller"))

    use_case.execute(_msg("si"))

    assert use_case.last_usage() is None


def test_rejected_message_reports_no_usage():
    use_case = _use_case()
    use_case.execute(_msg("crea la tarea Taller"))

    use_case.execute(_msg("x" * 1001))

    assert use_case.last_usage() is None
