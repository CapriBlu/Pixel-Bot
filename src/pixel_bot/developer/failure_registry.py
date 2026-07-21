from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FailureRegistry:
    """Persist diagnostic failures inside the Pixel-Bot workspace.

    Compatibility guarantees:
    - exposes both ``path`` and ``registry_path``;
    - creates the registry directory during initialization;
    - accepts text or structured Python payloads;
    - returns the path of the written file.
    """

    workspace: str | Path
    path: Path = field(init=False)
    registry_path: Path = field(init=False)
    failures: list[Path] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        workspace_path = Path(self.workspace)
        registry = workspace_path / "test-failure-registry"
        self.path = registry
        self.registry_path = registry
        self.ensure_exists()

    def ensure_exists(self) -> Path:
        self.registry_path.mkdir(parents=True, exist_ok=True)
        return self.registry_path

    @staticmethod
    def _serialize(payload: Any) -> tuple[str, str]:
        if isinstance(payload, str):
            return payload, ".txt"

        try:
            return (
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                ".json",
            )
        except (TypeError, ValueError):
            return str(payload), ".txt"

    @staticmethod
    def _safe_name(name: str) -> str:
        cleaned = "".join(
            char if char.isalnum() or char in {"-", "_", "."} else "_"
            for char in str(name).strip()
        )
        return cleaned or "failure"

    def record(self, name: str, payload: Any) -> Path:
        self.ensure_exists()

        content, default_suffix = self._serialize(payload)
        safe_name = self._safe_name(name)
        target = self.registry_path / safe_name

        if target.suffix == "":
            target = target.with_suffix(default_suffix)

        target.write_text(content, encoding="utf-8")
        self.failures.append(target)
        return target

    def record_failure(self, name: str, payload: Any) -> Path:
        """Backward-compatible alias used by older Pixel-Bot components."""
        return self.record(name, payload)

    def record_exception(self, name: str, error: BaseException) -> Path:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__,
            "message": str(error),
        }
        return self.record(name, payload)
