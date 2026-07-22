from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


class WatchdogTimeout(TimeoutError):
    """Raised when the autonomous loop stops reporting progress."""


@dataclass(slots=True)
class LoopWatchdog:
    timeout_seconds: float = 120.0
    clock: Callable[[], float] = time.monotonic
    started_at: float = field(init=False)
    last_progress: float = field(init=False)
    current_step: int | None = None
    phase: str = "idle"
    interventions: int = 0

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve essere maggiore di zero")
        now = self.clock()
        self.started_at = now
        self.last_progress = now

    def touch(self, *, step_id: int | None = None, phase: str | None = None) -> None:
        self.last_progress = self.clock()
        if step_id is not None:
            self.current_step = step_id
        if phase is not None:
            self.phase = phase

    def elapsed_without_progress(self) -> float:
        return max(0.0, self.clock() - self.last_progress)

    def check(self) -> None:
        elapsed = self.elapsed_without_progress()
        if elapsed > self.timeout_seconds:
            self.interventions += 1
            raise WatchdogTimeout(
                f"watchdog timeout dopo {elapsed:.3f}s senza progressi "
                f"(step={self.current_step}, phase={self.phase})"
            )
