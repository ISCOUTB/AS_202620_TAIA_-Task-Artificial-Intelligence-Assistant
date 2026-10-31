"""Cliente HTTP generado desde docs/api/openapi.json. NO EDITAR A MANO.

Regenerar con: python tools/generate_api_client.py
"""

from __future__ import annotations

import json
from urllib import error, request

PATH_ACADEMIC_TASKS = "/academic/tasks"
PATH_ACADEMIC_TASKS_TASK_ID = "/academic/tasks/{task_id}"
PATH_ACADEMIC_SUBJECTS = "/academic/subjects"
PATH_ACADEMIC_SUBJECTS_SUBJECT_ID = "/academic/subjects/{subject_id}"
PATH_ACADEMIC_SCHEDULE_BLOCKS = "/academic/schedule-blocks"
PATH_ACADEMIC_SCHEDULE_BLOCKS_BLOCK_ID = "/academic/schedule-blocks/{block_id}"
PATH_ACADEMIC_PERIOD = "/academic/period"
PATH_REMINDERS = "/reminders"
PATH_REMINDERS_REMINDER_ID = "/reminders/{reminder_id}"


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

    def register_task_academic_tasks_post(self, body: object | None = None) -> object:
        return self._request("POST", PATH_ACADEMIC_TASKS, body, **{})

    def list_tasks_academic_tasks_get(self, body: object | None = None) -> object:
        return self._request("GET", PATH_ACADEMIC_TASKS, body, **{})

    def get_task_academic_tasks__task_id__get(self, body: object | None = None, task_id: object | None = None) -> object:
        return self._request("GET", PATH_ACADEMIC_TASKS_TASK_ID, body, **{'task_id': task_id})

    def update_task_academic_tasks__task_id__patch(self, body: object | None = None, task_id: object | None = None) -> object:
        return self._request("PATCH", PATH_ACADEMIC_TASKS_TASK_ID, body, **{'task_id': task_id})

    def delete_task_academic_tasks__task_id__delete(self, body: object | None = None, task_id: object | None = None) -> object:
        return self._request("DELETE", PATH_ACADEMIC_TASKS_TASK_ID, body, **{'task_id': task_id})

    def complete_task_academic_tasks__task_id__complete_patch(self, body: object | None = None, task_id: object | None = None) -> object:
        return self._request("PATCH", "/academic/tasks/{task_id}/complete", body, **{'task_id': task_id})

    def reopen_task_academic_tasks__task_id__reopen_patch(self, body: object | None = None, task_id: object | None = None) -> object:
        return self._request("PATCH", "/academic/tasks/{task_id}/reopen", body, **{'task_id': task_id})

    def create_subject_academic_subjects_post(self, body: object | None = None) -> object:
        return self._request("POST", PATH_ACADEMIC_SUBJECTS, body, **{})

    def list_subjects_academic_subjects_get(self, body: object | None = None) -> object:
        return self._request("GET", PATH_ACADEMIC_SUBJECTS, body, **{})

    def get_subject_academic_subjects__subject_id__get(self, body: object | None = None, subject_id: object | None = None) -> object:
        return self._request("GET", PATH_ACADEMIC_SUBJECTS_SUBJECT_ID, body, **{'subject_id': subject_id})

    def update_subject_academic_subjects__subject_id__patch(self, body: object | None = None, subject_id: object | None = None) -> object:
        return self._request("PATCH", PATH_ACADEMIC_SUBJECTS_SUBJECT_ID, body, **{'subject_id': subject_id})

    def delete_subject_academic_subjects__subject_id__delete(self, body: object | None = None, subject_id: object | None = None) -> object:
        return self._request("DELETE", PATH_ACADEMIC_SUBJECTS_SUBJECT_ID, body, **{'subject_id': subject_id})

    def archive_subject_academic_subjects__subject_id__archive_post(self, body: object | None = None, subject_id: object | None = None) -> object:
        return self._request("POST", "/academic/subjects/{subject_id}/archive", body, **{'subject_id': subject_id})

    def unarchive_subject_academic_subjects__subject_id__unarchive_post(self, body: object | None = None, subject_id: object | None = None) -> object:
        return self._request("POST", "/academic/subjects/{subject_id}/unarchive", body, **{'subject_id': subject_id})

    def add_subject_alias_academic_subjects__subject_id__aliases_post(self, body: object | None = None, subject_id: object | None = None) -> object:
        return self._request("POST", "/academic/subjects/{subject_id}/aliases", body, **{'subject_id': subject_id})

    def remove_subject_alias_academic_subjects__subject_id__aliases__alias_id__delete(self, body: object | None = None, subject_id: object | None = None, alias_id: object | None = None) -> object:
        return self._request("DELETE", "/academic/subjects/{subject_id}/aliases/{alias_id}", body, **{'subject_id': subject_id, 'alias_id': alias_id})

    def create_schedule_block_academic_schedule_blocks_post(self, body: object | None = None) -> object:
        return self._request("POST", PATH_ACADEMIC_SCHEDULE_BLOCKS, body, **{})

    def list_schedule_blocks_academic_schedule_blocks_get(self, body: object | None = None) -> object:
        return self._request("GET", PATH_ACADEMIC_SCHEDULE_BLOCKS, body, **{})

    def update_schedule_block_academic_schedule_blocks__block_id__patch(self, body: object | None = None, block_id: object | None = None) -> object:
        return self._request("PATCH", PATH_ACADEMIC_SCHEDULE_BLOCKS_BLOCK_ID, body, **{'block_id': block_id})

    def delete_schedule_block_academic_schedule_blocks__block_id__delete(self, body: object | None = None, block_id: object | None = None) -> object:
        return self._request("DELETE", PATH_ACADEMIC_SCHEDULE_BLOCKS_BLOCK_ID, body, **{'block_id': block_id})

    def get_academic_period_academic_period_get(self, body: object | None = None) -> object:
        return self._request("GET", PATH_ACADEMIC_PERIOD, body, **{})

    def set_academic_period_academic_period_put(self, body: object | None = None) -> object:
        return self._request("PUT", PATH_ACADEMIC_PERIOD, body, **{})

    def register_user_users_post(self, body: object | None = None) -> object:
        return self._request("POST", "/users", body, **{})

    def login_user_users_login_post(self, body: object | None = None) -> object:
        return self._request("POST", "/users/login", body, **{})

    def get_current_user_users_me_get(self, body: object | None = None) -> object:
        return self._request("GET", "/users/me", body, **{})

    def create_telegram_link_users_me_telegram_link_post(self, body: object | None = None) -> object:
        return self._request("POST", "/users/me/telegram/link", body, **{})

    def telegram_webhook_telegram_webhook_post(self, body: object | None = None) -> object:
        return self._request("POST", "/telegram/webhook", body, **{})

    def handle_message_ai_message_post(self, body: object | None = None) -> object:
        return self._request("POST", "/ai/message", body, **{})

    def list_reminders_reminders_get(self, body: object | None = None) -> object:
        return self._request("GET", PATH_REMINDERS, body, **{})

    def create_reminder_reminders_post(self, body: object | None = None) -> object:
        return self._request("POST", PATH_REMINDERS, body, **{})

    def get_reminder_reminders__reminder_id__get(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("GET", PATH_REMINDERS_REMINDER_ID, body, **{'reminder_id': reminder_id})

    def edit_reminder_reminders__reminder_id__patch(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("PATCH", PATH_REMINDERS_REMINDER_ID, body, **{'reminder_id': reminder_id})

    def delete_reminder_reminders__reminder_id__delete(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("DELETE", PATH_REMINDERS_REMINDER_ID, body, **{'reminder_id': reminder_id})

    def mark_reminder_completed_reminders__reminder_id__complete_post(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("POST", "/reminders/{reminder_id}/complete", body, **{'reminder_id': reminder_id})

    def notify_reminder_reminders__reminder_id__notify_post(self, body: object | None = None, reminder_id: object | None = None) -> object:
        return self._request("POST", "/reminders/{reminder_id}/notify", body, **{'reminder_id': reminder_id})

    def health_health_get(self, body: object | None = None) -> object:
        return self._request("GET", "/health", body, **{})

    def mockup_mockup_get(self, body: object | None = None) -> object:
        return self._request("GET", "/mockup", body, **{})

