"""Pruebas de contrato entre la especificación OpenAPI y la API implementada."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re

import pytest

from backend.app.main import app


CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs/api/openapi.json"


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _assert_contract_matches(contract: dict, implementation: dict) -> None:
    assert contract["openapi"].startswith("3.1.")
    assert contract["info"]["version"] == "1.0.0"
    assert contract["paths"] == implementation["paths"]
    assert contract["components"] == implementation["components"]
    assert contract["info"] == implementation["info"]


def test_openapi_contract_matches_implemented_api() -> None:
    contract = _load_contract()
    implementation = app.openapi()
    _assert_contract_matches(contract, implementation)


def test_contract_declares_paths_and_data_schemas() -> None:
    contract = _load_contract()
    assert len(contract["paths"]) >= 10
    schemas = contract["components"]["schemas"]
    assert {"TaskCreateRequest", "TaskResponse", "AIMessageRequest", "AIMessageResponse"} <= set(schemas)


def test_incompatible_change_is_detected() -> None:
    """Demuestra que un cambio incompatible en el proveedor rompe la prueba."""
    contract = _load_contract()
    incompatible_implementation = copy.deepcopy(app.openapi())
    del incompatible_implementation["paths"]["/health"]

    with pytest.raises(AssertionError):
        _assert_contract_matches(contract, incompatible_implementation)


def test_generated_client_contains_all_contract_operations() -> None:
    contract = _load_contract()
    generated_client = (
        Path(__file__).resolve().parents[1] / "generated/taia_api_client.py"
    ).read_text(encoding="utf-8")
    for operations in contract["paths"].values():
        for operation in operations.values():
            operation_id = re.sub(
                r"[^0-9a-zA-Z_]+", "_", operation["operationId"]
            ).strip("_")
            assert f"def {operation_id}(" in generated_client
