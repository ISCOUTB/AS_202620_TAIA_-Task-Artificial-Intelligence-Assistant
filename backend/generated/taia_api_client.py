"""Cliente HTTP generado desde docs/api/openapi.json. NO EDITAR A MANO.

Regenerar con: python tools/generate_api_client.py
"""

from __future__ import annotations

import json
from urllib import error, request


class TaiaApiError(RuntimeError):
    """Error HTTP devuelto por la API TAIA."""

    def __init__(self, status: int, body: object):
        self.status = status
        self.body = body
        super().__init__(f"TAIA API returned HTTP {status}: {body}")


class TaiaApiClient:
    """Cliente generado para la API declarada en el contrato OpenAPI."""

    def __init__(self, base_url: str, access_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    def _request(self, method: str, path: str, body: object | None = None, **path_params: object) -> object:
        for name, value in path_params.items():
            path = path.replace("{" + name + "}", str(value))
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = response.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except error.HTTPError as exc:
            raw = exc.read()
            try:
                body = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                body = raw.decode("utf-8", errors="replace")
            raise TaiaApiError(exc.code, body) from exc

    def list_tasks_academic_tasks_get(self, body: object | None = None) -> object:
        return self._request("GET", "/academic/tasks", body, **{})

    def register_task_academic_tasks_post(self, body: object | None = None) -> object:
        return self._request("POST", "/academic/tasks", body, **{})

    def complete_task_academic_tasks__task_id__complete_patch(self, body: object | None = None, task_id: object | None = None) -> object:
        return self._request("PATCH", "/academic/tasks/{task_id}/complete", body, **{'task_id': task_id})

    def update_task_academic_tasks__task_id__patch(self, body: object | None = None, task_id: object | None = None) -> object:
        return self._request("PATCH", "/academic/tasks/{task_id}", body, **{'task_id': task_id})

    def register_user_users_post(self, body: object | None = None) -> object:
        return self._request("POST", "/users", body, **{})

    def login_user_users_login_post(self, body: object | None = None) -> object:
        return self._request("POST", "/users/login", body, **{})

    def get_current_user_users_me_get(self, body: object | None = None) -> object:
        return self._request("GET", "/users/me", body, **{})

    def create_telegram_link_users_me_telegram_link_post(self, body: object | None = None) -> object:
        return self._request("POST", "/users/me/telegram/link", body, **{})

    def confirm_telegram_link_users_telegram_link_confirm_post(self, body: object | None = None) -> object:
        return self._request("POST", "/users/telegram/link/confirm", body, **{})

    def handle_message_ai_message_post(self, body: object | None = None) -> object:
        return self._request("POST", "/ai/message", body, **{})

    def list_reminders_reminders_get(self, body: object | None = None) -> object:
        return self._request("GET", "/reminders", body, **{})

    def create_reminder_reminders_post(self, body: object | None = None) -> object:
        return self._request("POST", "/reminders", body, **{})

    def get_reminder_reminders__reminder_id__get(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("GET", "/reminders/{reminder_id}", body, **{'reminder_id': reminder_id})

    def edit_reminder_reminders__reminder_id__patch(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("PATCH", "/reminders/{reminder_id}", body, **{'reminder_id': reminder_id})

    def delete_reminder_reminders__reminder_id__delete(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("DELETE", "/reminders/{reminder_id}", body, **{'reminder_id': reminder_id})

    def mark_reminder_completed_reminders__reminder_id__complete_post(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("POST", "/reminders/{reminder_id}/complete", body, **{'reminder_id': reminder_id})

    def notify_reminder_reminders__reminder_id__notify_post(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("POST", "/reminders/{reminder_id}/notify", body, **{'reminder_id': reminder_id})

    def health_health_get(self, body: object | None = None) -> object:
        return self._request("GET", "/health", body, **{})

