"""Comprueba un recorrido real usando exclusivamente una cuenta nueva de pruebas."""
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

BASE = "http://taia-sistema-jkbo9i-ec2cd4-144-24-4-187.sslip.io"
ROOT = Path(__file__).resolve().parents[1]


def main():
    run = uuid.uuid4().hex[:12]
    email = f"eval-{run}@example.com"
    password = secrets.token_urlsafe(32)
    with httpx.Client(base_url=BASE, timeout=60) as c:
        user = c.post("/users", json={"full_name": "Evaluación S1", "email": email, "password": password})
        print("register", user.status_code, flush=True)
        user.raise_for_status()
        auth = c.post("/users/login", json={"email": email, "password": password})
        auth.raise_for_status()
        c.headers["Authorization"] = "Bearer " + auth.json()["access_token"]
        subject = c.post("/academic/subjects", json={"name": "Matemáticas"})
        subject.raise_for_status()
        due = (datetime.now(timezone(timedelta(hours=-5))) + timedelta(days=20)).replace(hour=17, minute=0, second=0, microsecond=0)
        payload = {"text": f'Crea una tarea titulada "Resolver integrales" de Matemáticas para el {due.date()} a las 17:00.', "channel": "app"}
        response = c.post("/ai/message", json=payload)
        print("ai", response.status_code, response.text, flush=True)
        session = {"base_url": BASE, "email": email, "password": password,
                   "user_id": user.json()["id"], "subject_id": subject.json()["id"]}
        private = ROOT / ".venv" / "api_eval_session.json"
        private.write_text(json.dumps(session), encoding="utf-8")
        if response.is_success and response.json().get("awaiting_confirmation"):
            confirmed = c.post("/ai/message", json={"text": "Sí", "channel": "app"})
            print("confirm", confirmed.status_code, confirmed.text, flush=True)
            tasks = c.get("/academic/tasks").json()
            print("persisted", json.dumps(tasks, ensure_ascii=False), flush=True)
            for task in tasks.get("items", []):
                deleted = c.delete("/academic/tasks/" + task["id"])
                print("cleanup", deleted.status_code, flush=True)


if __name__ == "__main__":
    main()
