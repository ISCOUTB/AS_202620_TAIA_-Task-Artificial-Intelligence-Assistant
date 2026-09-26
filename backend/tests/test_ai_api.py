from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.modules.ai.adapters.inbound.api import get_ai_use_case
from app.modules.ai.adapters.outbound.academic_gateway import AcademicGatewayAdapter
from app.modules.ai.adapters.outbound.in_memory_conversation_store import InMemoryConversationStore
from app.modules.ai.adapters.outbound.fake_llm import FakeLLM
from app.modules.ai.application.use_cases.handle_message import HandleUserMessageUseCase
from app.modules.ai.domain.messages import ExtractedTaskData, Interpretation, Intent

client = TestClient(app)
TZ = timezone(timedelta(hours=-5))


def register_and_login(email: str) -> dict[str, str]:
    created = client.post(
        "/users",
        json={"full_name": "Estudiante", "email": email, "password": "password123"},
    )
    assert created.status_code == 201
    login = client.post(
        "/users/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_ai_endpoint_requires_authentication():
    response = client.post("/ai/message", json={"text": "mis tareas"})
    assert response.status_code == 401


def test_ai_create_task_uses_real_academic_context(monkeypatch):
    headers = register_and_login("ai-api@example.com")
    subject = client.post("/academic/subjects", json={"name": "Arquitectura"}, headers=headers)
    assert subject.status_code == 201
    llm = FakeLLM(
        [
            Interpretation(
                intent=Intent.CREATE_TASK,
                confidence=0.95,
                task=ExtractedTaskData(
                    title="Tarea creada por IA",
                    due_at=datetime.now(TZ) + timedelta(days=5),
                    subject="Arquitectura",
                ),
            )
        ]
    )
    use_case = HandleUserMessageUseCase(
        llm=llm,
        academic=AcademicGatewayAdapter(),
        conversations=InMemoryConversationStore(),
    )
    app.dependency_overrides[get_ai_use_case] = lambda: use_case
    try:
        proposed = client.post(
            "/ai/message",
            json={"text": "crea una tarea de arquitectura"},
            headers=headers,
        )
        assert proposed.status_code == 200
        assert proposed.json()["awaiting_confirmation"] is True

        confirmed = client.post(
            "/ai/message",
            json={"text": "si"},
            headers=headers,
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["awaiting_confirmation"] is False
        assert "Tarea creada por IA" in confirmed.json()["text"]

        academic = client.get("/academic/tasks", headers=headers)
        assert academic.status_code == 200
        created = [task for task in academic.json()["items"] if task["title"] == "Tarea creada por IA"]
        assert created[0]["subject_name"] == "Arquitectura"
    finally:
        app.dependency_overrides.pop(get_ai_use_case, None)
