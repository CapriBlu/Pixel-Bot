from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DevelopmentTask:
    task_id: str
    title: str
    objective: str
    acceptance_criteria: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=lambda: ["src", "tests", "docs", "tasks"])
    test_command: list[str] = field(default_factory=lambda: ["pytest", "-q"])
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RepositorySnapshot:
    root: Path
    files: list[str]
    python_files: list[str]
    test_files: list[str]
    task_files: list[str]


@dataclass(slots=True)
class DevelopmentPlan:
    task: DevelopmentTask
    relevant_files: list[str]
    steps: list[str]
    risks: list[str] = field(default_factory=list)
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": {
                "task_id": self.task.task_id,
                "title": self.task.title,
                "objective": self.task.objective,
                "acceptance_criteria": self.task.acceptance_criteria,
                "allowed_paths": self.task.allowed_paths,
                "test_command": self.task.test_command,
                "metadata": self.task.metadata,
            },
            "relevant_files": self.relevant_files,
            "steps": self.steps,
            "risks": self.risks,
            "status": self.status,
        }


@dataclass(slots=True)
class TestResult:
    command: list[str]
    return_code: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.return_code == 0
