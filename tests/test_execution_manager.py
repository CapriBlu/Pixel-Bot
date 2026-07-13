from unittest.mock import patch

import pytest

from pixel_bot.core.execution_manager import ExecutionManager
from pixel_bot.core.planner import Planner


@patch("pixel_bot.core.execution_manager.execute_action")
def test_execute_complete_plan(mock_execute):
    events = []

    manager = ExecutionManager(
        event_callback=lambda name, payload: events.append(name)
    )

    plan = Planner().create_plan(
        "screenshot; aspetta 1 secondo"
    )

    manager.start(plan)
    manager.wait(timeout=2)

    assert manager.state.status == "completed"
    assert plan.status == "completed"

    assert all(
        step.status == "completed"
        for step in plan.steps
    )

    assert "execution_started" in events
    assert "execution_completed" in events
    assert mock_execute.call_count == 2


@patch("pixel_bot.core.execution_manager.execute_action")
def test_execution_failure(mock_execute):
    mock_execute.side_effect = RuntimeError("Errore simulato")

    manager = ExecutionManager()
    plan = Planner().create_plan("screenshot")

    manager.start(plan)
    manager.wait(timeout=2)

    assert manager.state.status == "failed"
    assert manager.state.error == "Errore simulato"
    assert plan.status == "failed"


@patch("pixel_bot.core.execution_manager.execute_action")
def test_reject_second_execution(mock_execute):
    manager = ExecutionManager()
    plan = Planner().create_plan("aspetta 1 secondo")

    manager.state.status = "running"

    with pytest.raises(RuntimeError):
        manager.start(plan)


def test_stop_when_idle():
    manager = ExecutionManager()

    manager.stop()

    assert manager.state.status == "idle"