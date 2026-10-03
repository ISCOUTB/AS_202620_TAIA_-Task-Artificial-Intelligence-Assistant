"""D-S8-01: la confirmacion de una escritura debe entender acentos, mayusculas y signos.

Un estudiante escribe en espanol y confirma con "Sí". El caso de uso normaliza
solo con `.lower().strip(" .!?")`, de modo que "Sí" queda como "sí" y no coincide
con el conjunto _YES, que solo contiene "si" sin tilde. La tarea nunca se crea y
el estudiante recibe una peticion de confirmar sobre una peticion de confirmar.

Cada caso ejecuta el flujo real: una primera mensaje que deja la accion
pendiente y un segundo mensaje de respuesta.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.adapters.outbound.in_memory_academic_gateway import (
    InMemoryAcademicGateway,
)
from app.modules.ai.adapters.outbound.in_memory_conversation_store import (
    InMemoryConversationStore,
)
from app.modules.ai.application.dto import TaskFilters
from app.modules.ai.application.use_cases.handle_message import (
    HandleUserMessageUseCase,
)
from app.modules.ai.domain.messages import (
    Channel,
    ExtractedTaskData,
    IncomingRequest,
    Intent,
    Interpretation,
)

TZ = timezone(timedelta(hours=-5))
DUE = datetime(2026, 9, 20, 20, 0, tzinfo=TZ)

CONFIRMAN = [
    pytest.param("sí", id="acentuada-minuscula"),
    pytest.param("Sí", id="acentuada-capitalizada"),
    pytest.param("SÍ", id="acentuida-mayuscula"),
    pytest.param("Si", id="sin-tilde-capitalizada"),
    pytest.param("SI", id="sin-tilde-mayuscula"),
    pytest.param("sí.", id="acentuada-con-punto"),
    pytest.param("  sí  ", id="acentuada-con-espacios"),
    pytest.param("sí!", id="acentuada-con-exclamacion"),
    pytest.param("¡Sí!", id="acentuada-con-exclamaciones"),
    pytest.param("dale", id="afirmativo-alternativo"),
]

NO_CONFIRMAN = [
    pytest.param("no", id="negativo"),
    pytest.param("cancelar", id="negativo-alternativo"),
    pytest.param("nop", id="negativo-typo"),
    pytest.param("no, después", id="negativo-con-frase"),
    pytest.param("más tarde", id="aplazamiento"),
    pytest.param("crea otra cosa", id="mensaje-distinto"),
]


def _montar():
    academic = InMemoryAcademicGateway()
    store = InMemoryConversationStore()
    caso = HandleUserMessageUseCase(
        llm=FakeLLM(
            [
                Interpretation(
                    Intent.CREATE_TASK,
                    0.9,
                    task=ExtractedTaskData(title="Taller", due_at=DUE),
                )
            ]
        ),
        academic=academic,
        conversations=store,
        now=lambda: datetime(2026, 9, 10, 12, 0, tzinfo=TZ),
    )
    caso.execute(
        IncomingRequest(user_id="u1", text="crea la tarea taller", channel=Channel.TELEGRAM)
    )
    return caso, academic


@pytest.mark.parametrize("respuesta", CONFIRMAN)
def test_confirmacion_crea_la_tarea(respuesta):
    caso, academic = _montar()

    reply = caso.execute(
        IncomingRequest(user_id="u1", text=respuesta, channel=Channel.TELEGRAM)
    )

    tareas = academic.list_tasks("u1", TaskFilters())
    assert len(tareas) == 1, f"{respuesta!r} no creo la tarea: {reply.text!r}"
    assert tareas[0].title == "Taller"
    assert "cree la tarea" in reply.text.lower()


@pytest.mark.parametrize("respuesta", NO_CONFIRMAN)
def test_una_respuesta_negativa_no_crea_la_tarea(respuesta):
    caso, academic = _montar()

    caso.execute(
        IncomingRequest(user_id="u1", text=respuesta, channel=Channel.TELEGRAM)
    )

    assert academic.list_tasks("u1", TaskFilters()) == []