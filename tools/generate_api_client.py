"""Genera un cliente HTTP mínimo a partir del contrato OpenAPI de TAIA.

Uso:
    python tools/generate_api_client.py

El archivo generado no contiene reglas de negocio; solo refleja la superficie
HTTP declarada en docs/api/openapi.json.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/api/openapi.json"
OUTPUT = ROOT / "backend/generated/taia_api_client.py"


def method_name(operation_id: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", operation_id).strip("_")
    if name and name[0].isdigit():
        name = f"operation_{name}"
    return name or "operation"


def generate() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    methods: list[tuple[str, str, str]] = []
    for path, operations in contract["paths"].items():
        for http_method, operation in operations.items():
            if http_method.lower() not in {"get", "post", "patch", "put", "delete"}:
                continue
            methods.append((http_method.upper(), path, method_name(operation["operationId"])))

    lines = [
        '"""Cliente HTTP generado desde docs/api/openapi.json. NO EDITAR A MANO.',
        "",
        "Regenerar con: python tools/generate_api_client.py",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "import json",
        "from urllib import error, request",
        "",
        "",
        "class TaiaApiError(RuntimeError):",
        "    \"\"\"Error HTTP devuelto por la API TAIA.\"\"\"",
        "",
        "    def __init__(self, status: int, body: object):",
        "        self.status = status",
        "        self.body = body",
        "        super().__init__(f\"TAIA API returned HTTP {status}: {body}\")",
        "",
        "",
        "class TaiaApiClient:",
        '    """Cliente generado para la API declarada en el contrato OpenAPI."""',
        "",
        "    def __init__(self, base_url: str, access_token: str | None = None):",
        '        self.base_url = base_url.rstrip("/")',
        "        self.access_token = access_token",
        "",
        "    def _request(self, method: str, path: str, body: object | None = None, **path_params: object) -> object:",
        "        for name, value in path_params.items():",
        '            path = path.replace("{" + name + "}", str(value))',
        '        url = f"{self.base_url}{path}"',
        '        headers = {"Accept": "application/json"}',
        "        if body is not None:",
        '            headers["Content-Type"] = "application/json"',
        "        if self.access_token:",
        '            headers["Authorization"] = f"Bearer {self.access_token}"',
        '        data = None if body is None else json.dumps(body).encode("utf-8")',
        "        req = request.Request(url, data=data, headers=headers, method=method)",
        "        try:",
        "            with request.urlopen(req, timeout=30) as response:",
        "                raw = response.read()",
        "                if not raw:",
        "                    return None",
        "                return json.loads(raw.decode(\"utf-8\"))",
        "        except error.HTTPError as exc:",
        "            raw = exc.read()",
        "            try:",
        "                body = json.loads(raw.decode(\"utf-8\"))",
        "            except json.JSONDecodeError:",
        "                body = raw.decode(\"utf-8\", errors=\"replace\")",
        "            raise TaiaApiError(exc.code, body) from exc",
        "",
    ]

    for http_method, path, name in methods:
        params = [p for p in re.findall(r"{([^}]+)}", path)]
        signature = [f"self", "body: object | None = None"] + [f"{p}: object | None = None" for p in params]
        lines += [
            f"    def {name}({', '.join(signature)}) -> object:",
            f'        return self._request("{http_method}", "{path}", body, **{{{", ".join(f"{p!r}: {p}" for p in params)}}})',
            "",
        ]

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {len(methods)} operations -> {OUTPUT}")


if __name__ == "__main__":
    generate()
