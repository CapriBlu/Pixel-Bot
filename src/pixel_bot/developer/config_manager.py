from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class FoundationConfig:
    watchdog_timeout_seconds: float = 120.0
    max_attempts: int = 3
    max_rounds: int = 20
    journal_enabled: bool = True
    dashboard_history_limit: int = 250
    health_sample_seconds: float = 5.0

    def validate(self) -> None:
        if self.watchdog_timeout_seconds <= 0 or self.health_sample_seconds <= 0:
            raise ValueError("I timeout devono essere positivi")
        if self.max_attempts < 1 or self.max_rounds < 1:
            raise ValueError("I limiti devono essere almeno 1")
        if self.dashboard_history_limit < 1:
            raise ValueError("dashboard_history_limit deve essere almeno 1")


class ConfigManager:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> FoundationConfig:
        if not self.path.exists():
            config = FoundationConfig()
            self.save(config)
            return config
        data = json.loads(self.path.read_text(encoding="utf-8"))
        config = FoundationConfig(**data)
        config.validate()
        return config

    def save(self, config: FoundationConfig) -> None:
        config.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
        temp.replace(self.path)
