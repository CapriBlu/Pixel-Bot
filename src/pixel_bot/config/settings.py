from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} deve essere un intero.") from exc
    if value <= 0:
        raise ValueError(f"{name} deve essere maggiore di zero.")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    normalized = raw.strip().casefold()
    if normalized in {"1", "true", "yes", "on", "si", "sì"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} deve essere un valore booleano.")


@dataclass(slots=True, frozen=True)
class PixelBotSettings:
    project_root: Path
    screenshots_dir: Path
    logs_dir: Path
    workspace_dir: Path
    default_monitor: int = 1
    log_level: str = "INFO"
    structured_logging: bool = False

    @classmethod
    def from_env(cls, project_root: str | Path | None = None) -> "PixelBotSettings":
        root = Path(project_root or os.getenv("PIXELBOT_PROJECT_ROOT") or Path.cwd())
        root = root.expanduser().resolve()
        log_level = os.getenv("PIXELBOT_LOG_LEVEL", "INFO").strip().upper() or "INFO"
        return cls(
            project_root=root,
            screenshots_dir=root / os.getenv("PIXELBOT_SCREENSHOTS_DIR", "screenshots"),
            logs_dir=root / os.getenv("PIXELBOT_LOGS_DIR", "logs"),
            workspace_dir=root / os.getenv("PIXELBOT_WORKSPACE_DIR", "workspace"),
            default_monitor=_env_int("PIXELBOT_DEFAULT_MONITOR", 1),
            log_level=log_level,
            structured_logging=_env_bool("PIXELBOT_STRUCTURED_LOGGING", False),
        )

    def ensure_runtime_directories(self) -> None:
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)


_SETTINGS: PixelBotSettings | None = None


def get_settings(*, refresh: bool = False) -> PixelBotSettings:
    global _SETTINGS
    if refresh or _SETTINGS is None:
        _SETTINGS = PixelBotSettings.from_env()
    return _SETTINGS
