from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.shared.adapters.inbound import readiness


@pytest.mark.parametrize("available,expected", [(True, 200), (False, 503)])
def test_health_checks_database_and_does_not_expose_driver_details(monkeypatch, available, expected):
    engine = MagicMock()
    if not available:
        engine.connect.side_effect = OperationalError("internal details", {}, Exception("private data"))
    monkeypatch.setattr(readiness, "get_engine", lambda: engine)
    app = FastAPI()

    @app.get("/health")
    def health(ready: None = Depends(readiness.require_database)):
        return {"status": "ok"}

    response = TestClient(app).get("/health")
    assert response.status_code == expected
    assert "private data" not in response.text
    assert "internal details" not in response.text
    if available:
        engine.connect.return_value.__enter__.return_value.execute.assert_called_once()
