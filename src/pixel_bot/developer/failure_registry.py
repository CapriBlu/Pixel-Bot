from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class FailureRegistry:
    """Registry to store failures for developer tasks.

    The class is a dataclass with slots enabled. To avoid AttributeError when
    assigning computed attributes (which are not part of the init), we declare
    the attribute using dataclasses.field(init=False) and set its value in
    __post_init__.

    The registry_path is computed relative to the provided repository_root as
    repository_root / "workspace" / "test-failure-registry".
    """

    repository_root: Path
    path: Path = field(init=False)

    def __post_init__(self) -> None:
        # Normalize repository_root and compute the registry path explicitly
        self.repository_root = Path(self.repository_root).resolve()
        self.path = self.repository_root / "workspace" / "test-failure-registry"

    def ensure_exists(self) -> None:
        """Create the registry directory if it doesn't exist."""
        self.path.mkdir(parents=True, exist_ok=True)

    def clear(self) -> None:
        """Remove all files in the registry directory (does not remove the dir)."""
        if not self.path.is_dir():
            return
        for child in self.path.iterdir():
            try:
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    # remove directory contents recursively
                    for sub in child.rglob("*"):
                        if sub.is_file():
                            sub.unlink()
                    # attempt to remove the directory itself
                    try:
                        child.rmdir()
                    except Exception:
                        pass
            except Exception:
                # Best-effort cleanup; avoid raising to keep registry robust
                pass

    def record(self, name: str, content: str) -> Path:
        """Record a failure payload to a file inside the registry.

        Returns the path to the written file.
        """
        self.ensure_exists()
        target = self.path / name
        target.write_text(content, encoding="utf-8")
        return target

    def list_entries(self) -> list[Path]:
        """Return a sorted list of files directly under the registry directory."""
        if not self.path.is_dir():
            return []
        return sorted([p for p in self.path.iterdir() if p.is_file()])
