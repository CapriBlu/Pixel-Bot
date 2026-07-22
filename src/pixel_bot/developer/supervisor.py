from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pixel_bot.agent.budget import BudgetState

RepositoryCheck = Callable[[], tuple[bool, str | None]]


@dataclass(slots=True)
class SessionSupervisor:
    """Safety supervisor evaluated before every autonomous queue task."""

    stop_file: Path
    pause_file: Path
    state_path: Path
    budget: BudgetState | None = None
    repository_check: RepositoryCheck | None = None

    def __post_init__(self) -> None:
        self.stop_file = self.stop_file.resolve()
        self.pause_file = self.pause_file.resolve()
        self.state_path = self.state_path.resolve()

    def check(self) -> str | None:
        if self.stop_file.exists():
            return self._record("stopped_by_request")
        if self.pause_file.exists():
            return self._record("paused")
        if self.budget is not None:
            if self.budget.requests_used >= self.budget.max_requests:
                return self._record("session_request_budget_exhausted")
            next_cost = self.budget.estimated_cost_used + self.budget.estimated_cost_per_request
            if next_cost > self.budget.max_estimated_cost:
                return self._record("session_cost_budget_exhausted")
        if self.repository_check is not None:
            safe, detail = self.repository_check()
            if not safe:
                return self._record("unsafe_repository_state", detail)
        self._record("running")
        return None

    def finish(self, status: str) -> None:
        self._record(status)

    def _record(self, status: str, detail: str | None = None) -> str:
        payload = {
            "status": status,
            "detail": detail,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "budget": None if self.budget is None else self.budget.to_dict(),
            "stop_file": str(self.stop_file),
            "pause_file": str(self.pause_file),
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.state_path)
        return status
