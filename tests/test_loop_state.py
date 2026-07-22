import pytest

from pixel_bot.developer.loop_state import (
    LoopStatus,
    StepStatus,
    coerce_loop_status,
    coerce_step_status,
)


def test_status_values_are_stable_strings():
    assert str(LoopStatus.RUNNING) == "running"
    assert str(StepStatus.VERIFYING) == "verifying"


def test_unknown_statuses_are_rejected():
    with pytest.raises(ValueError, match="sconosciuto"):
        coerce_loop_status("mystery")
    with pytest.raises(ValueError, match="sconosciuto"):
        coerce_step_status("mystery")
