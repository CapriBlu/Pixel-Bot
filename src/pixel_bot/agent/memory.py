from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AgentMemory:
    path: Path
    entries: list[dict[str, Any]] = field(default_factory=list)
    max_entries: int = 500

    def load(self) -> None:
        if not self.path.exists():
            self.entries = []
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("Il file di memoria deve contenere una lista.")
        self.entries = [item for item in payload if isinstance(item, dict)][
            -self.max_entries :
        ]

    def append(self, entry: dict[str, Any]) -> None:
        if not isinstance(entry, dict):
            raise TypeError("La voce di memoria deve essere un dizionario.")
        self.entries.append(entry.copy())
        self.entries = self.entries[-self.max_entries :]
        self.save()

    def extend(self, entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            if isinstance(entry, dict):
                self.entries.append(entry.copy())
        self.entries = self.entries[-self.max_entries :]
        self.save()

    def recent(self, limit: int = 12) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        return [entry.copy() for entry in self.entries[-limit:]]

    def clear(self) -> None:
        self.entries = []
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
