"""Logs estructurados, métrica de latencia (S3, RNF-08) y secreto JWT obligatorio (RNF-02)."""

from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.usuario.adapters.outbound.jwt_token_service import JwtTokenService
from app.shared.adapters.inbound.observability import JsonFormatter, metrics
from helpers import register_and_login

client = TestClient(app)


def _request_logs(caplog) -> list[dict]:
    formatter = JsonFormatter()
    return [
        json.loads(formatter.format(record))
        for record in caplog.records
        if record.name == "taia" and record.getMessage() == "http_request"
    ]


@pytest.fixture
def taia_logs(caplog):
    # El logger "taia" no propaga al raíz; caplog se conecta directamente.
    logger = logging.getLogger("taia")
    logger.addHandler(caplog.handler)
    yield caplog
    logger.removeHandler(caplog.handler)


def test_each_request_emits_one_json_line_with_fields(taia_logs):
    client.get("/health")

    entry = _request_logs(taia_logs)[-1]
    assert entry["event"] == "http_request"
    assert entry["method"] == "GET"
    assert entry["route"] == "/health"
    assert entry["status"] == 200
    assert isinstance(entry["duration_ms"], float)
    assert entry["user_id"] is None
    assert entry["timestamp"].endswith("-05:00")


def test_log_uses_route_template_and_authenticated_user_id(taia_logs):
    headers = register_and_login(client)
    me = client.get("/users/me", headers=headers).json()

    client.get("/reminders/00000000-0000-0000-0000-000000000000", headers=headers)

    entry = _request_logs(taia_logs)[-1]
    assert entry["route"] == "/reminders/{reminder_id}"
    assert entry["user_id"] == me["id"]


def test_log_never_contains_request_body_or_token(taia_logs):
    headers = register_and_login(client)

    raw = [JsonFormatter().format(record) for record in taia_logs.records if record.name == "taia"]
    assert raw
    token = headers["Authorization"].removeprefix("Bearer ")
    assert all("password123" not in line and token not in line for line in raw)


def test_metrics_reports_p95_against_scenario_targets():
    metrics.reset()
    client.get("/health")
    client.post("/ai/message", json={"message": "hola"})

    body = client.get("/metrics").json()
    health = body["routes"]["GET /health"]
    agent = body["routes"]["POST /ai/message"]

    assert body["metric"] == "http_request_duration_p95_ms"
    assert health["requests"] == 1
    assert health["target_p95_ms"] == 500
    assert health["quality_reference"] == "RNF-08"
    assert health["within_target"] is True
    assert agent["target_p95_ms"] == 7000
    assert agent["quality_reference"] == "S3"


def test_metrics_is_public_and_outside_the_contract():
    assert client.get("/metrics").status_code == 200
    assert "/metrics" not in app.openapi()["paths"]


def test_jwt_service_refuses_to_start_without_secret(monkeypatch):
    monkeypatch.delenv("TAIA_JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="TAIA_JWT_SECRET"):
        JwtTokenService()
