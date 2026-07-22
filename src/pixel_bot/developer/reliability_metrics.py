from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ReliabilitySnapshot:
    tasks_started: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    steps_completed: int = 0
    retries: int = 0
    execution_failures: int = 0
    verification_failures: int = 0
    verification_errors: int = 0
    resumes: int = 0
    watchdog_interventions: int = 0
    total_step_duration_seconds: float = 0.0
    measured_steps: int = 0

    @property
    def task_success_rate(self) -> float:
        finished = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / finished if finished else 0.0

    @property
    def average_step_duration(self) -> float:
        return self.total_step_duration_seconds / self.measured_steps if self.measured_steps else 0.0

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["task_success_rate"] = self.task_success_rate
        data["average_step_duration"] = self.average_step_duration
        return data


class ReliabilityMetrics:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.snapshot = self._load() if path and path.exists() else ReliabilitySnapshot()

    def increment(self, field: str, amount: int = 1) -> None:
        if not hasattr(self.snapshot, field):
            raise AttributeError(field)
        setattr(self.snapshot, field, int(getattr(self.snapshot, field)) + amount)
        self.save()

    def record_step_duration(self, seconds: float) -> None:
        self.snapshot.total_step_duration_seconds += max(0.0, float(seconds))
        self.snapshot.measured_steps += 1
        self.save()

    def save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.snapshot.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _load(self) -> ReliabilitySnapshot:
        assert self.path is not None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        allowed = ReliabilitySnapshot.__dataclass_fields__
        return ReliabilitySnapshot(**{key: value for key, value in data.items() if key in allowed})
