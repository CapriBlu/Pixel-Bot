from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    goal: str
    status: str = "pending"
    current_step: int = 0
    context: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PersistentTaskMemory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: TaskRecord) -> None:
        record.updated_at = datetime.now(timezone.utc).isoformat()
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> TaskRecord | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return TaskRecord(**data)

    def append_event(self, record: TaskRecord, event: str, **payload: Any) -> None:
        record.history.append({
            "at": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        })
        self.save(record)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
