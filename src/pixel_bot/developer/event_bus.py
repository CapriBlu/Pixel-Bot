from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class Event:
    sequence: int
    type: str
    timestamp: str
    payload: dict[str, Any]


class EventBus:
    """Event bus sincrono, thread-safe e con journal JSONL opzionale."""

    def __init__(self, journal_path: Path | None = None) -> None:
        self.journal_path = journal_path
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self._sequence = 0
        self._lock = RLock()

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> Callable[[], None]:
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(callback)
        def unsubscribe() -> None:
            with self._lock:
                callbacks = self._subscribers.get(event_type, [])
                if callback in callbacks:
                    callbacks.remove(callback)
        return unsubscribe

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> Event:
        if not event_type.strip():
            raise ValueError("event_type non può essere vuoto")
        with self._lock:
            self._sequence += 1
            event = Event(self._sequence, event_type, datetime.now(timezone.utc).isoformat(), dict(payload or {}))
            callbacks = list(self._subscribers.get(event_type, [])) + list(self._subscribers.get("*", []))
            self._append(event)
        for callback in callbacks:
            callback(event)
        return event

    def _append(self, event: Event) -> None:
        if self.journal_path is None:
            return
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        with self.journal_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    @staticmethod
    def read_journal(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows[-limit:] if limit else rows
