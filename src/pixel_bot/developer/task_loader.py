from __future__ import annotations

import json
from pathlib import Path

from pixel_bot.developer.models import DevelopmentTask


class TaskLoader:
    def __init__(self, tasks_dir: Path) -> None:
        self.tasks_dir = tasks_dir

    def list_tasks(self) -> list[Path]:
        if not self.tasks_dir.exists():
            return []
        return sorted(self.tasks_dir.glob("*.json"))

    def load(self, path: Path) -> DevelopmentTask:
        resolved = path.resolve()
