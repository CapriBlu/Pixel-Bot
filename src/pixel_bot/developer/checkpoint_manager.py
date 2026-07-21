from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .task_memory import TaskRecord


@dataclass(slots=True)
class Checkpoint:
    version: int
    reason: str
    saved_at: str
    task: dict[str, Any]
    active_step: int | None = None
    active_attempt: int | None = None


class CheckpointManager:
    VERSION = 1

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        record: TaskRecord,
        reason: str,
        *,
        active_step: int | None = None,
        active_attempt: int | None = None,
    ) -> Checkpoint:
        checkpoint = Checkpoint(
            version=self.VERSION,
            reason=reason,
            saved_at=datetime.now(timezone.utc).isoformat(),
            task=asdict(record),
            active_step=active_step,
            active_attempt=active_attempt,
        )
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(checkpoint), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
        return checkpoint

    def load(self) -> Checkpoint | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if int(data.get("version", 0)) != self.VERSION:
            raise ValueError("Versione checkpoint non supportata")
        return Checkpoint(**data)

    def restore_record(self) -> TaskRecord | None:
        checkpoint = self.load()
        if checkpoint is None:
            return None
        return TaskRecord(**checkpoint.task)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
