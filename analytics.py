"""
analytics.py
============
Lightweight, dependency-free analytics engine for tracking AI usage.

Every AI request (chat message or playground run) is recorded as an
`AnalyticsEvent` and persisted to a JSON file on disk (see `config.data_dir`).
This module intentionally avoids a database dependency to keep the project
trivial to run locally -- swap `JsonEventStore` for a real database-backed
store in production without touching the rest of the codebase.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config import MODEL_PRICING, DEFAULT_PRICING, config

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsEvent:
    """A single recorded AI request."""

    id: str
    timestamp: str  # ISO 8601 UTC
    model: str
    category: str  # e.g. "chat", "playground"
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time_ms: int
    estimated_cost: float
    success: bool = True
    prompt_preview: str = ""

    @staticmethod
    def new(
        model: str,
        category: str,
        prompt_tokens: int,
        completion_tokens: int,
        response_time_ms: int,
        prompt_preview: str = "",
        success: bool = True,
    ) -> "AnalyticsEvent":
        total = prompt_tokens + completion_tokens
        cost = estimate_cost(model, prompt_tokens, completion_tokens)
        return AnalyticsEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=model,
            category=category,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            response_time_ms=response_time_ms,
            estimated_cost=cost,
            success=success,
            prompt_preview=prompt_preview[:160],
        )


def estimate_tokens(text: str) -> int:
    """Very rough token estimate (~4 characters per token heuristic).

    This avoids adding a heavyweight tokenizer dependency. It is accurate
    enough for dashboard/analytics display purposes but should not be relied
    on for billing-grade precision.
    """
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    cost = (prompt_tokens / 1000) * pricing.prompt_per_1k
    cost += (completion_tokens / 1000) * pricing.completion_per_1k
    return round(cost, 6)


class JsonEventStore:
    """Thread-safe append-only JSON file store for analytics events."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write(self, events: list[dict[str, Any]]) -> None:
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(events, fh, indent=2)

    def append(self, event: AnalyticsEvent) -> None:
        with self._lock:
            events = self._read()
            events.append(asdict(event))
            # Cap history to the most recent 5,000 events to keep file size sane.
            events = events[-5000:]
            self._write(events)
            logger.info(
                "analytics_event_recorded model=%s category=%s tokens=%s cost=%.6f",
                event.model,
                event.category,
                event.total_tokens,
                event.estimated_cost,
            )

    def all(self) -> list[AnalyticsEvent]:
        with self._lock:
            return [AnalyticsEvent(**e) for e in self._read()]


class AnalyticsEngine:
    """Computes aggregate statistics on top of the raw event store."""

    def __init__(self, store: JsonEventStore | None = None):
        self.store = store or JsonEventStore(config.data_dir / "analytics_events.json")

    def record(
        self,
        model: str,
        category: str,
        prompt_tokens: int,
        completion_tokens: int,
        response_time_ms: int,
        prompt_preview: str = "",
        success: bool = True,
    ) -> AnalyticsEvent:
        event = AnalyticsEvent.new(
            model=model,
            category=category,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            response_time_ms=response_time_ms,
            prompt_preview=prompt_preview,
            success=success,
        )
        self.store.append(event)
        return event

    # ------------------------------------------------------------------
    # Aggregate queries
    # ------------------------------------------------------------------
    def _events_since(self, days: int) -> list[AnalyticsEvent]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = []
        for e in self.store.all():
            try:
                ts = datetime.fromisoformat(e.timestamp)
            except ValueError:
                continue
            if ts >= cutoff:
                result.append(e)
        return result

    def summary(self) -> dict[str, Any]:
        """High level KPI numbers used by the dashboard stat cards."""
        all_events = self.store.all()
        today = self._events_since(1)
        week = self._events_since(7)
        month = self._events_since(30)

        def agg(events: list[AnalyticsEvent]) -> dict[str, Any]:
            total_tokens = sum(e.total_tokens for e in events)
            total_cost = sum(e.estimated_cost for e in events)
            avg_time = (
                sum(e.response_time_ms for e in events) / len(events) if events else 0
            )
            return {
                "requests": len(events),
                "tokens": total_tokens,
                "cost": round(total_cost, 4),
                "avg_response_ms": round(avg_time, 1),
            }

        return {
            "today": agg(today),
            "week": agg(week),
            "month": agg(month),
            "all_time": agg(all_events),
        }

    def requests_over_time(self, days: int = 14) -> dict[str, list]:
        """Daily request counts for the last N days, oldest first."""
        events = self._events_since(days)
        buckets: dict[str, int] = defaultdict(int)
        for e in events:
            day = e.timestamp[:10]
            buckets[day] += 1

        labels = []
        values = []
        for i in range(days - 1, -1, -1):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            labels.append(day)
            values.append(buckets.get(day, 0))
        return {"labels": labels, "values": values}

    def token_usage_over_time(self, days: int = 14) -> dict[str, list]:
        events = self._events_since(days)
        prompt_buckets: dict[str, int] = defaultdict(int)
        completion_buckets: dict[str, int] = defaultdict(int)
        for e in events:
            day = e.timestamp[:10]
            prompt_buckets[day] += e.prompt_tokens
            completion_buckets[day] += e.completion_tokens

        labels, prompt_vals, completion_vals = [], [], []
        for i in range(days - 1, -1, -1):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            labels.append(day)
            prompt_vals.append(prompt_buckets.get(day, 0))
            completion_vals.append(completion_buckets.get(day, 0))
        return {"labels": labels, "prompt_tokens": prompt_vals, "completion_tokens": completion_vals}

    def cost_over_time(self, days: int = 14) -> dict[str, list]:
        events = self._events_since(days)
        buckets: dict[str, float] = defaultdict(float)
        for e in events:
            day = e.timestamp[:10]
            buckets[day] += e.estimated_cost

        labels, values = [], []
        for i in range(days - 1, -1, -1):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            labels.append(day)
            values.append(round(buckets.get(day, 0.0), 4))
        return {"labels": labels, "values": values}

    def response_times(self, days: int = 14) -> dict[str, list]:
        events = self._events_since(days)
        buckets: dict[str, list[int]] = defaultdict(list)
        for e in events:
            day = e.timestamp[:10]
            buckets[day].append(e.response_time_ms)

        labels, values = [], []
        for i in range(days - 1, -1, -1):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            labels.append(day)
            times = buckets.get(day, [])
            values.append(round(sum(times) / len(times), 1) if times else 0)
        return {"labels": labels, "values": values}

    def prompt_categories(self) -> dict[str, list]:
        events = self.store.all()
        counts = Counter(e.category or "uncategorized" for e in events)
        if not counts:
            return {"labels": [], "values": []}
        labels, values = zip(*counts.most_common())
        return {"labels": list(labels), "values": list(values)}

    def most_used_prompts(self, limit: int = 5) -> list[dict[str, Any]]:
        events = self.store.all()
        counts = Counter(e.prompt_preview for e in events if e.prompt_preview)
        return [
            {"prompt": prompt, "count": count}
            for prompt, count in counts.most_common(limit)
        ]

    def recent_activity(self, limit: int = 10) -> list[dict[str, Any]]:
        events = sorted(self.store.all(), key=lambda e: e.timestamp, reverse=True)
        return [asdict(e) for e in events[:limit]]


analytics_engine = AnalyticsEngine()
