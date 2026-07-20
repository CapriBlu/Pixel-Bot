from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FailureRegistry:
    """Registry for storing failure artifacts inside a workspace.

    The class is a dataclass with slots enabled. To avoid AttributeError when
    setting computed attributes in __post_init__, those attributes must be
    declared as dataclass fields (even if they are init=False). This class
    declares `registry_path` as an init=False field and initializes it in
    __post_init__ based on the provided `workspace`.
    """

    workspace: Path
    registry_path: Path = field(init=False)

    def __post_init__(self) -> None:
        # Normalize workspace path
        self.workspace = Path(self.workspace)
        # Compute and ensure the registry directory exists
        self.registry_path = self.workspace / "test-failure-registry"
        self.registry_path.mkdir(parents=True, exist_ok=True)

    def record(self, name: str, payload: Any) -> Path:
        """Persist a failure payload as JSON under the registry.

        Returns the path to the written file.
        """
        target = self.registry_path / f"{name}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target
