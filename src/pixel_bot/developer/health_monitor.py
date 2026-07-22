from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class HealthSnapshot:
    timestamp: str
    pid: int
    uptime_seconds: float
    load_average_1m: float | None
    status: str
    details: dict[str, Any]


class HealthMonitor:
    def __init__(self) -> None:
        self._started = time.monotonic()

    def sample(self, **details: Any) -> HealthSnapshot:
        load: float | None = None
        if hasattr(os, "getloadavg"):
            try:
                load = float(os.getloadavg()[0])
            except OSError:
                load = None
        status = "degraded" if details.get("watchdog_tripped") else "healthy"
        return HealthSnapshot(datetime.now(timezone.utc).isoformat(), os.getpid(), time.monotonic() - self._started, load, status, details)

    @staticmethod
    def as_dict(snapshot: HealthSnapshot) -> dict[str, Any]:
        return asdict(snapshot)
