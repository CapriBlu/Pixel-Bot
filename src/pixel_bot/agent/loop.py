from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pixel_bot.agent.models import AgentDecision
from pixel_bot.core.executor import execute_action
from pixel_bot.core.safety import Action, validate_action
from pixel_bot.vision.screen_capture import capture_screen


class DecisionProvider(Protocol):
    def decide(
        self,
        *,
        goal: str,
        screenshot_path: Path,
        history: list[dict[str, Any]],
    ) -> AgentDecision: ...


ConfirmationCallback = Callable[[Action, AgentDecision], bool]
EventCallback = Callable[[str, dict[str, Any]], None]


@dataclass(slots=True)
class AgentLoopResult:
    status: str
    steps: int
    history: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class AgentLoop:
    def __init__(
        self,
        decision_provider