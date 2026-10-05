"""Ejecuta las regresiones de fronteras sobre HEAD sin modificar el árbol.

Uso: python tools/demo_s8_red.py
Resultado esperado antes de incorporar la corrección: 3 failed, salida 1.
Después: python -m pytest backend/tests/test_s8_closure.py -q
"""

from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    ROOT / "backend/app/modules/academic/adapters/inbound/structure_api.py",
    ROOT / "backend/app/modules/reminders/adapters/inbound/http_controller.py",
    ROOT / "backend/app/modules/ai/adapters/outbound/academic_gateway.py",
}
original_read = Path.read_text


def read_baseline(path, *args, **kwargs):
    if path.resolve() in FILES:
        relative = path.resolve().relative_to(ROOT).as_posix()
        return subprocess.check_output(
            ["git", "show", f"HEAD:{relative}"], cwd=ROOT, encoding="utf-8")
    return original_read(path, *args, **kwargs)


if __name__ == "__main__":
    print("Baseline:", subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), flush=True)
    with patch.object(Path, "read_text", read_baseline):
        raise SystemExit(pytest.main([
            str(ROOT / "backend/tests/test_s8_closure.py"),
            "-k", "controllers or public_inbound_contract",
            "-q", "-p", "no:cacheprovider",
        ]))
