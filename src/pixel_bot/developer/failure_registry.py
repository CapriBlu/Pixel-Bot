from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(slots=True)
class FailureRegistry:
    """Registry of failures persisted under a workspace directory.

    This class is a dataclass with slots enabled. To allow assigning the
    computed registry path in __post_init__ we declare registry_path as a
    dataclass field with init=False. The registry directory is created on
    initialization.
    """

    workspace: Path
    name: str = "test-failure-registry"
    registry_path: Path = field(init=False)
    failures: Dict[str, List[str]] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        # Ensure workspace is a Path and exists
        self.workspace = Path(self.workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Compute and expose the registry path as an attribute declared on the dataclass
        self.registry_path = (self.workspace / self.name).resolve()
        self.registry_path.mkdir(parents=True, exist_ok=True)

        # Load existing failures if present
        self._load()

    def add_failure(self, key: str, message: str) -> None:
        """Record a failure message under the provided key and persist."""
        self.failures.setdefault(key, []).append(message)
        self._persist()

    def _persist(self) -> None:
        file_path = self.registry_path / "failures.json"
        file_path.write_text(json.dumps(self.failures, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> None:
        file_path = self.registry_path / "failures.json"
        if file_path.is_file():
            try:
                self.failures = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                # If the file is corrupt or unreadable, start with an empty registry
                self.failures = {}

    def get_failures(self, key: str) -> List[str]:
        return list(self.failures.get(key, []))
