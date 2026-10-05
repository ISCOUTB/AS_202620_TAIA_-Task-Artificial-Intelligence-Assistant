"""S4: 100 accesos sobre tareas de dos cuentas sintéticas, con limpieza acotada."""
import json
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    session = json.loads((ROOT / ".venv/api_eval_session.json").read_text(encoding="utf-8"))
    started = datetime.now(timezone.utc)
    identifier = uuid.uuid4().hex[:10]
    output = ROOT / f"docs/evaluacion_ia/aislamiento_{identifier}.json"
    records, created, cleanup = [], [], []
    with httpx.Client(base_url=session["base_url"], timeout=30) as owner, httpx.Client(
        base_url=session["base_url"], timeout=30
    ) as other:
        login = owner.post("/users/login", json={
            "email": session["email"], "password": session["password"]})
        login.raise_for_status()
        owner.headers["Authorization"] = "Bearer " + login.json()["access_token"]
        password = secrets.token_urlsafe(32)
        email = f"isolation-{identifier}@example.com"
        registered = other.post("/users", json={
            "full_name": "Evaluación aislamiento", "email": email, "password": password})
        registered.raise_for_status()
        login = other.post("/users/login", json={"email": email, "password": password})
        login.raise_for_status()
        other.headers["Authorization"] = "Bearer " + login.json()["access_token"]
        try:
            for index in range(25):
                response = owner.post("/academic/tasks", json={
                    "subject_id": session["subject_id"],
                    "title": f"Evaluación de propiedad {identifier}-{index}",
                    "due_at": (started + timedelta(days=30)).isoformat()})
                response.raise_for_status()
                created.append(response.json()["id"])
            for index, task_id in enumerate(created):
                path = "/academic/tasks/" + task_id
                for client, kind, method in [
                    (owner, "autorizado", "GET"), (other, "ajeno", "GET"),
                    (owner, "autorizado", "PATCH"), (other, "ajeno", "PATCH"),
                ]:
                    before = time.perf_counter()
                    kwargs = {"json": {"description": kind}} if method == "PATCH" else {}
                    response = client.request(method, path, **kwargs)
                    valid = response.status_code == (200 if kind == "autorizado" else 404)
                    if kind == "ajeno":
                        valid = valid and task_id not in response.text and "Evaluación de propiedad" not in response.text
                    records.append({"caso": index, "actor": kind, "metodo": method,
                                    "status": response.status_code, "correcto": valid,
                                    "latencia_ms": round((time.perf_counter() - before) * 1000, 1)})
                # Comprueba que la escritura denegada no cambió el registro.
                verification = owner.get(path)
                verification.raise_for_status()
                records[-1]["correcto"] &= verification.json()["description"] == "autorizado"
                print(f"casos comprobados {len(records)}/100", flush=True)
        finally:
            for task_id in created:
                response = owner.delete("/academic/tasks/" + task_id)
                cleanup.append({"id": task_id, "status": response.status_code})
            result = {
                "fecha_utc": started.isoformat(), "base_url": session["base_url"],
                "escenario": "S4 - API HTTP, lectura y edición entre dos usuarios",
                "alcance": "25 tareas; 50 accesos propios y 50 ajenos; sin consulta conversacional LLM",
                "casos": records, "total": len(records),
                "correctos": sum(r["correcto"] for r in records),
                "umbral_rechazo_ajenos": 1.0,
                "cumple_corte_http": len(records) == 100 and all(r["correcto"] for r in records),
                "cumple_escenario_con_llm": None,
                "limpieza_tareas": cleanup,
                "cuentas_sinteticas_restantes": 2,
                "nota_limpieza": "La API no ofrece eliminación de cuentas; las tareas se eliminan lógicamente.",
            }
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"evidencia {output.name}: {result['correctos']}/{len(records)}", flush=True)


if __name__ == "__main__":
    main()
