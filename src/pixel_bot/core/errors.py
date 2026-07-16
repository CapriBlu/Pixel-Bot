from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PixelBotError(Exception):
    message: str
    code: str = "pixelbot_error"
    recoverable: bool = False
    context: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "recoverable": self.recoverable,
            "context": dict(self.context or {}),
        }


class ConfigurationError(PixelBotError):
    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message, "configuration_error", False, context)


class ScreenCaptureError(PixelBotError):
    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message, "screen_capture_error", True, context)


class AutomationError(PixelBotError):
    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message, "automation_error", True, context)
