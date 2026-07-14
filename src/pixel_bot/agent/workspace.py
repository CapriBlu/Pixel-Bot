from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AgentWorkspace:
    root: Path = Path("workspace")

    def initialize(self) -> None:
        for name in (
            "screenshots",
            "history",
            "memory",
            "plans",
            "patches",
            "logs",
            "cache",
            "tasks",
        ):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def write_json(self, section: str, name: str, payload: Any) -> Path:
        self.initialize()
        target_dir = (self.root / section).resolve()
        root = self.root.resolve()
        if root not in target_dir.parents:
            raise ValueError("Sezione workspace non valida.")
        target = target_dir / name
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target

    def save_run(self, goal: str, result: dict[str, Any]) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return self.write_json(
            "history",
            f"run_{timestamp}.json",
            {"goal": goal, **result},
        )
