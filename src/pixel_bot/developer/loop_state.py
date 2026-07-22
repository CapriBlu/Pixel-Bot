from __future__ import annotations

from enum import StrEnum


class LoopStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    VERIFYING = "verifying"
    RETRYING = "retrying"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    BOUNDED = "bounded"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    VERIFYING = "verifying"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"


TERMINAL_LOOP_STATUSES = {
    LoopStatus.COMPLETED,
    LoopStatus.FAILED,
    LoopStatus.BOUNDED,
    LoopStatus.CANCELLED,
}


def coerce_loop_status(value: str | LoopStatus) -> LoopStatus:
    try:
        return value if isinstance(value, LoopStatus) else LoopStatus(value)
    except ValueError as exc:
        raise ValueError(f"Stato del loop sconosciuto: {value!r}") from exc


def coerce_step_status(value: str | StepStatus) -> StepStatus:
    try:
        return value if isinstance(value, StepStatus) else StepStatus(value)
    except ValueError as exc:
        raise ValueError(f"Stato del passaggio sconosciuto: {value!r}") from exc
