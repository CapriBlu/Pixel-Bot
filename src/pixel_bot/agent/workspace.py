from __future__ import annotations

import json
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKSPACE_SECTIONS = (
    "screenshots",
    "history",
    "memory",
    "plans",
    "patches",
    "logs",
    "cache",
    "tasks",
    "sessions",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Workspace:
    root: Path = Path("workspace")
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @classmethod
    def temporary(cls) -> "Workspace":
        return cls(root=Path(tempfile.mkdtemp(prefix="pixel_bot_")))

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in WORKSPACE_SECTIONS:
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    @property
    def session_dir(self) -> Path:
        return self.root / "sessions" / self.session_id

    @property
    def events_path(self) -> Path:
        return self.session_dir / "events.jsonl"

    @property
    def summary_path(self) -> Path:
        return self.session_dir / "summary.json"

    @property
    def memory_path(self) -> Path:
        return self.session_dir / "memory.json"

    def safe_path(self, section: str, name: str) -> Path:
        self.initialize()
        if section not in WORKSPACE_SECTIONS:
            raise ValueError(f"Sezione workspace non autorizzata: {section}")
        if not name or Path(name).name != name:
            raise ValueError("Nome file non valido.")
        target = (self.root / section / name).resolve()
        section_root = (self.root / section).resolve()
        if target.parent != section_root:
            raise ValueError("Percorso workspace non valido.")
        return target

    def write_json(self, section: str, name: str, payload: Any) -> Path:
        target = self.safe_path(section, name)
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target

    def append_event(self, event: str, payload: dict[str, Any] | None = None) -> Path:
        self.initialize()
        record = {
            "timestamp": _utc_now(),
            "session_id": self.session_id,
            "event": event,
            "payload": payload or {},
        }
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return self.events_path

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit <= 0 or not self.events_path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
        return records[-limit:]

    def save_summary(self, payload: dict[str, Any]) -> Path:
        self.initialize()
        summary = {
            "session_id": self.session_id,
            "updated_at": _utc_now(),
            **payload,
        }
        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.summary_path


# Backward-compatible alias used by early prototypes.
AgentWorkspace = Workspace
