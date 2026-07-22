from __future__ import annotations

import json
from pathlib import Path

from pixel_bot.agent.budget import BudgetState
from pixel_bot.developer.supervisor import SessionSupervisor


def test_supervisor_stops_and_persists_state(tmp_path: Path) -> None:
    stop_file = tmp_path / "STOP"
    stop_file.write_text("stop", encoding="utf-8")
    state = tmp_path / "state.json"
    supervisor = SessionSupervisor(stop_file, tmp_path / "PAUSE", state)

    assert supervisor.check() == "stopped_by_request"
    assert json.loads(state.read_text(encoding="utf-8"))["status"] == "stopped_by_request"


def test_supervisor_pauses_before_repository_check(tmp_path: Path) -> None:
    pause_file = tmp_path / "PAUSE"
    pause_file.write_text("pause", encoding="utf-8")
    called = False

    def repository_check():
        nonlocal called
        called = True
        return False, "dirty"

    supervisor = SessionSupervisor(tmp_path / "STOP", pause_file, tmp_path / "state.json", repository_check=repository_check)
    assert supervisor.check() == "paused"
    assert called is False


def test_supervisor_enforces_session_budget(tmp_path: Path) -> None:
    budget = BudgetState(max_requests=1, max_estimated_cost=1.0, estimated_cost_per_request=0.1)
    budget.record_request()
    supervisor = SessionSupervisor(tmp_path / "STOP", tmp_path / "PAUSE", tmp_path / "state.json", budget=budget)

    assert supervisor.check() == "session_request_budget_exhausted"


def test_supervisor_blocks_dirty_repository(tmp_path: Path) -> None:
    supervisor = SessionSupervisor(
        tmp_path / "STOP",
        tmp_path / "PAUSE",
        tmp_path / "state.json",
        repository_check=lambda: (False, "Working tree non pulito."),
    )

    assert supervisor.check() == "unsafe_repository_state"
    payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert payload["detail"] == "Working tree non pulito."
