from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AgentMemory:
    path: Path
    entries: list[dict[str, Any]] = field(default_factory=list)

    def load(self) -> None:
        if not self.path.exists():
            self.entries = []
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("Il file di memoria deve contenere una lista.")
        self.entries = [item for item in payload if isinstance(item, dict)]

    def append(self, entry: dict[str, Any]) -> None:
        self.entries.append(entry)
        self.save()

    def recent(self, limit: int = 12) -> list[dict[str, Any]]:
        return self.entries[-limit:]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
