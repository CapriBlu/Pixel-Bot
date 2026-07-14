from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pixel_bot.developer.models import DevelopmentTask
from pixel_bot.developer.task_loader import TaskLoader


@dataclass(slots=True)
class QueuedTask:
    path: Path
    task: DevelopmentTask
    priority: int
    attempts: int


class TaskQueue:
    """Persistent, deterministic queue for autonomous development tasks."""

    terminal_statuses = frozenset({"completed", "cancelled"})

    def __init__(
        self,
        tasks_dir: Path,
        state_path: Path,
        *,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts deve essere almeno 1.")
        self.tasks_dir = tasks_dir.resolve()
        self.state_path = state_path.resolve()
        self.max_attempts = max_attempts
        self.loader = TaskLoader(self.tasks_dir)

    def next_task(self) -> QueuedTask | None:
        state = self._read_state()
        candidates: list[QueuedTask] = []
        for path in self.loader.list_tasks():
            record = state.get(path.name, {})
            status = str(record.get("status", "pending"))
            attempts = int(record.get("attempts", 0))
            if status in self.terminal_statuses or attempts >= self.max_attempts:
                continue
            try:
                task = self.loader.load(path)
            except (OSError, ValueError, json.JSONDecodeError):
                # The tasks directory may also contain fixtures such as
                # ``*.changes.json``. Invalid task documents are ignored.
                continue
            priority = self._priority(task.metadata.get("priority", 100))
            candidates.append(QueuedTask(path, task, priority, attempts))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item.priority, item.task.task_id, item.path.name))
        return candidates[0]

    def mark_started(self, queued: QueuedTask) -> None:
        state = self._read_state()
        record = state.setdefault(queued.path.name, {})
        record.update(
            {
                "task_id": queued.task.task_id,
                "status": "in_progress",
                "attempts": int(record.get("attempts", 0)) + 1,
                "last_error": None,
            }
        )
        self._write_state(state)

    def mark_completed(self, queued: QueuedTask, report_path: Path | None = None) -> None:
        state = self._read_state()
        record = state.setdefault(queued.path.name, {})
        record.update(
            {
                "task_id": queued.task.task_id,
                "status": "completed",
                "report_path": None if report_path is None else str(report_path),
                "last_error": None,
            }
        )
        self._write_state(state)

    def mark_failed(self, queued: QueuedTask, error: str) -> None:
        state = self._read_state()
        record = state.setdefault(queued.path.name, {})
        attempts = int(record.get("attempts", 0))
        record.update(
            {
                "task_id": queued.task.task_id,
                "status": "failed" if attempts >= self.max_attempts else "pending",
                "last_error": error,
            }
        )
        self._write_state(state)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return self._read_state()

    @staticmethod
    def _priority(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 100

    def _read_state(self) -> dict[str, dict[str, Any]]:
        if not self.state_path.exists():
            return {}
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Lo stato della task queue deve essere un oggetto JSON.")
        return {
            str(name): dict(record)
            for name, record in payload.items()
            if isinstance(record, dict)
        }

    def _write_state(self, state: dict[str, dict[str, Any]]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.state_path)
