from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pixel_bot.developer.models import DevelopmentTask


class TaskLoader:
    def __init__(self, tasks_dir: Path) -> None:
        self.tasks_dir = tasks_dir.resolve()

    def list_tasks(self) -> list[Path]:
        if not self.tasks_dir.exists():
            return []
        return sorted(self.tasks_dir.glob("*.json"))

    def load(self, path: Path) -> DevelopmentTask:
        resolved = path.resolve()
        if self.tasks_dir != resolved.parent:
            raise ValueError("Il task deve trovarsi nella directory autorizzata.")
        payload = json.loads(resolved.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("Il task deve contenere un oggetto JSON.")
        return self.from_dict(payload)

    def load_next(self) -> DevelopmentTask | None:
        tasks = self.list_tasks()
        return self.load(tasks[0]) if tasks else None

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> DevelopmentTask:
        required = ("task_id", "title", "objective")
        missing = [name for name in required if not payload.get(name)]
        if missing:
            raise ValueError(f"Campi task mancanti: {', '.join(missing)}")

        criteria = payload.get("acceptance_criteria", [])
        allowed_paths = payload.get("allowed_paths", ["src", "tests", "docs", "tasks"])
        test_command = payload.get("test_command", ["pytest", "-q"])
        metadata = payload.get("metadata", {})

        if not all(isinstance(item, str) for item in criteria):
            raise ValueError("acceptance_criteria deve essere una lista di stringhe.")
        if not all(isinstance(item, str) for item in allowed_paths):
            raise ValueError("allowed_paths deve essere una lista di stringhe.")
        if not test_command or not all(isinstance(item, str) for item in test_command):
            raise ValueError("test_command deve essere una lista non vuota di stringhe.")
        if not isinstance(metadata, dict):
            raise ValueError("metadata deve essere un oggetto.")

        return DevelopmentTask(
            task_id=str(payload["task_id"]),
            title=str(payload["title"]),
            objective=str(payload["objective"]),
            acceptance_criteria=list(criteria),
            allowed_paths=list(allowed_paths),
            test_command=list(test_command),
            metadata=metadata,
        )
