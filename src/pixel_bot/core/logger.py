from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from pixel_bot.config import PixelBotSettings, get_settings

_CONFIGURED_PATH: Path | None = None


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if event is not None:
            payload["event"] = event
        context = getattr(record, "context", None)
        if context:
            payload["context"] = context
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(
    settings: PixelBotSettings | None = None,
    *,
    force: bool = False,
) -> Path:
    global _CONFIGURED_PATH
    settings = settings or get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = settings.logs_dir / "pixel_bot.log"

    root = logging.getLogger("pixel_bot")
    if force:
        for handler in root.handlers[:]:
            handler.close()
            root.removeHandler(handler)

    if not root.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        if settings.structured_logging:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
            )
        root.addHandler(handler)
        root.propagate = False

    level = getattr(logging, settings.log_level, logging.INFO)
    root.setLevel(level)
    _CONFIGURED_PATH = log_path
    return log_path


def get_logger(name: str) -> logging.Logger:
    if _CONFIGURED_PATH is None:
        configure_logging()
    if name.startswith("pixel_bot"):
        return logging.getLogger(name)
    return logging.getLogger(f"pixel_bot.{name}")


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **context: Any,
) -> None:
    logger.log(level, event, extra={"event": event, "context": context})
