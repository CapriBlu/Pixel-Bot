from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FailureRegistry:
    """Registry for test failures stored under a workspace directory.

    Notes:
    - When using dataclass(slots=True) any attribute assigned on the instance
      must be declared as a field. Previously the runtime attempted to set
      an attribute (e.g. `path` or `registry_path`) that wasn't declared,
      causing AttributeError. To avoid that we declare the attribute here
      with init=False and compute it in __post_init__.
    """

    workspace: Path | str
    # Declare the attribute that will be initialized in __post_init__ so
    # dataclass with slots=True allows assigning to it later.
    path: Path = field(init=False)
    # Keep the constant registry directory name explicit and configurable
    # (init=False so it is not part of the constructor signature).
    registry_dir_name: str = field(default="test-failure-registry", init=False)

    def __post_init__(self) -> None:
        # Accept either Path or str for workspace for convenience in tests
        if not isinstance(self.workspace, Path):
            self.workspace = Path(self.workspace)
        self.workspace = self.workspace.resolve()

        # Compute and initialize the declared path attribute
        self.path = self.workspace / self.registry_dir_name
        self.path.mkdir(parents=True, exist_ok=True)

    @property
    def registry_path(self) -> Path:
        """Backward-compatible accessor for the registry path."""
        return self.path

    def record_failure(self, name: str, payload: Any) -> Path:
        """Record a failure payload as JSON under the registry directory.

        Returns the path to the written file.
        """
        target = self.path / f"{name}.json"
        # Ensure parent exists (should already exist, but keep defensive)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def list_failures(self) -> list[Path]:
        """Return a sorted list of failure file paths contained in the registry."""
        if not self.path.exists():
            return []
        return sorted(p for p in self.path.iterdir() if p.is_file())
