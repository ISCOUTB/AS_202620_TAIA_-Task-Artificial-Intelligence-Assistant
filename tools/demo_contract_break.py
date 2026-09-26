"""Demostración reproducible: una ruptura incompatible hace fallar el contrato.

Este script se ejecuta manualmente para la evidencia S7 y NO forma parte del CI.
Debe terminar con código distinto de cero.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from backend.app.main import app
from backend.tests.test_api_contract import _assert_contract_matches

contract = json.loads(Path("docs/api/openapi.json").read_text(encoding="utf-8"))
broken_implementation = copy.deepcopy(app.openapi())
del broken_implementation["paths"]["/health"]

print("Cambio incompatible simulado: se elimina GET /health de la implementación.")
print("Ejecutando la misma comprobación usada por la prueba de contrato...")
_assert_contract_matches(contract, broken_implementation)
