from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pixel_bot.developer.models import RepositorySnapshot


@dataclass(slots=True)
class RepositoryAnalyzer:
    root: Path
    excluded_dirs: tuple[str, ...] = (
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "workspace",
        "dist",
        "build",
    )

    def analyze(self) -> RepositorySnapshot:
        root = self.root.resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Repository non trovato: {root}")
        files: list[str] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if any(part in self.excluded_dirs for part in relative.parts):
                continue
            files.append(relative.as_posix())
        files.sort()
        return RepositorySnapshot(
            root=root,
            files=files,
            python_files=[item for item in files if item.endswith(".py")],
            test_files=[item for item in files if item.startswith("tests/")],
            task_files=[item for item in files if item.startswith("tasks/")],
        )

    def relevant_files(self, objective: str, snapshot: RepositorySnapshot, limit: int = 20) -> list[str]:
        tokens = {
            token.lower().strip(".,:;()[]{}")
            for token in objective.split()
            if len(token.strip(".,:;()[]{}")) >= 4
        }
        scored: list[tuple[int, str]] = []
        for file_path in snapshot.files:
            lowered = file_path.lower()
            score = sum(1 for token in tokens if token in lowered)
            if file_path.startswith("src/"):
                score += 1
            if score:
                scored.append((score, file_path))
        scored.sort(key=lambda item: (-item[0], item[1]))
        selected = [path for _, path in scored[:limit]]
        if selected:
            return selected
        return snapshot.python_files[:limit]
