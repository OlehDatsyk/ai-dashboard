"""
dashboard_service.py
=====================
Application/domain services that back the dashboard UI:

- Saved / favorite prompt library (Prompt Playground)
- Prompt history
- Notifications feed
- User-configurable settings (model, temperature, system prompt, theme)

All state is persisted as JSON under `config.data_dir` so the project runs
with zero external database setup. Swap `JsonRepository` for a real
database-backed repository in production.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import config

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonRepository:
    """Generic thread-safe JSON list repository keyed by record `id`."""

    def __init__(self, path: Path, default: Any):
        self.path = path
        self._lock = threading.Lock()
        self._default = default
        if not self.path.exists():
            self._write(default)

    def read(self) -> Any:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._default

    def _write(self, data: Any) -> None:
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def write(self, data: Any) -> None:
        with self._lock:
            self._write(data)


@dataclass
class SavedPrompt:
    id: str
    title: str
    content: str
    category: str
    favorite: bool
    created_at: str
    updated_at: str

    @staticmethod
    def new(title: str, content: str, category: str = "general", favorite: bool = False) -> "SavedPrompt":
        now = _now_iso()
        return SavedPrompt(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            category=category,
            favorite=favorite,
            created_at=now,
            updated_at=now,
        )


@dataclass
class Notification:
    id: str
    title: str
    message: str
    level: str  # info | success | warning | error
    created_at: str
    read: bool = False

    @staticmethod
    def new(title: str, message: str, level: str = "info") -> "Notification":
        return Notification(
            id=str(uuid.uuid4()),
            title=title,
            message=message,
            level=level,
            created_at=_now_iso(),
            read=False,
        )


DEFAULT_SETTINGS = {
    "theme": "dark",
    "default_model": config.default_model,
    "default_temperature": config.default_temperature,
    "system_prompt": config.default_system_prompt,
    "display_name": "Alex Morgan",
    "email": "alex.morgan@example.com",
    "role": "AI Solutions Architect",
}

DEFAULT_NOTIFICATIONS = [
    {
        "id": str(uuid.uuid4()),
        "title": "Welcome to AI Dashboard",
        "message": "Your workspace is ready. Connect your OpenAI API key in Settings to unlock AI features.",
        "level": "info",
        "created_at": _now_iso(),
        "read": False,
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Weekly usage report",
        "message": "Your weekly AI usage analytics summary is ready to view.",
        "level": "success",
        "created_at": _now_iso(),
        "read": False,
    },
]

DEFAULT_PROMPT_TEMPLATES = [
    {
        "id": str(uuid.uuid4()),
        "title": "Bug triage summary",
        "content": (
            "Summarize the following bug report for an engineering standup. "
            "Include severity, likely root cause, and suggested owner:\n\n{{bug_report}}"
        ),
        "category": "engineering",
        "favorite": True,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Product changelog writer",
        "content": (
            "Turn the following raw commit messages into a concise, customer-facing "
            "changelog entry grouped by Added / Fixed / Improved:\n\n{{commits}}"
        ),
        "category": "product",
        "favorite": False,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    },
    {
        "id": str(uuid.uuid4()),
        "title": "SQL query explainer",
        "content": "Explain what the following SQL query does in plain English, step by step:\n\n{{sql}}",
        "category": "engineering",
        "favorite": True,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    },
]


class DashboardService:
    def __init__(self) -> None:
        self.prompts_repo = JsonRepository(config.data_dir / "prompts.json", DEFAULT_PROMPT_TEMPLATES)
        self.notifications_repo = JsonRepository(config.data_dir / "notifications.json", DEFAULT_NOTIFICATIONS)
        self.settings_repo = JsonRepository(config.data_dir / "settings.json", DEFAULT_SETTINGS)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------
    def list_prompts(self) -> list[dict[str, Any]]:
        return sorted(self.prompts_repo.read(), key=lambda p: p["updated_at"], reverse=True)

    def create_prompt(self, title: str, content: str, category: str = "general", favorite: bool = False) -> dict[str, Any]:
        prompts = self.prompts_repo.read()
        prompt = asdict(SavedPrompt.new(title=title, content=content, category=category, favorite=favorite))
        prompts.append(prompt)
        self.prompts_repo.write(prompts)
        return prompt

    def update_prompt(self, prompt_id: str, **updates: Any) -> dict[str, Any] | None:
        prompts = self.prompts_repo.read()
        for p in prompts:
            if p["id"] == prompt_id:
                p.update({k: v for k, v in updates.items() if v is not None})
                p["updated_at"] = _now_iso()
                self.prompts_repo.write(prompts)
                return p
        return None

    def toggle_favorite(self, prompt_id: str) -> dict[str, Any] | None:
        prompts = self.prompts_repo.read()
        for p in prompts:
            if p["id"] == prompt_id:
                p["favorite"] = not p["favorite"]
                p["updated_at"] = _now_iso()
                self.prompts_repo.write(prompts)
                return p
        return None

    def delete_prompt(self, prompt_id: str) -> bool:
        prompts = self.prompts_repo.read()
        filtered = [p for p in prompts if p["id"] != prompt_id]
        changed = len(filtered) != len(prompts)
        if changed:
            self.prompts_repo.write(filtered)
        return changed

    def favorite_prompts(self) -> list[dict[str, Any]]:
        return [p for p in self.list_prompts() if p.get("favorite")]

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    def list_notifications(self) -> list[dict[str, Any]]:
        return sorted(self.notifications_repo.read(), key=lambda n: n["created_at"], reverse=True)

    def unread_count(self) -> int:
        return sum(1 for n in self.notifications_repo.read() if not n.get("read"))

    def push_notification(self, title: str, message: str, level: str = "info") -> dict[str, Any]:
        notifications = self.notifications_repo.read()
        notification = asdict(Notification.new(title=title, message=message, level=level))
        notifications.append(notification)
        self.notifications_repo.write(notifications[-100:])
        return notification

    def mark_notification_read(self, notification_id: str) -> bool:
        notifications = self.notifications_repo.read()
        for n in notifications:
            if n["id"] == notification_id:
                n["read"] = True
                self.notifications_repo.write(notifications)
                return True
        return False

    def mark_all_read(self) -> None:
        notifications = self.notifications_repo.read()
        for n in notifications:
            n["read"] = True
        self.notifications_repo.write(notifications)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def get_settings(self) -> dict[str, Any]:
        settings = dict(DEFAULT_SETTINGS)
        settings.update(self.settings_repo.read())
        return settings

    def update_settings(self, **updates: Any) -> dict[str, Any]:
        settings = self.get_settings()
        settings.update({k: v for k, v in updates.items() if v is not None})
        self.settings_repo.write(settings)
        return settings


dashboard_service = DashboardService()
