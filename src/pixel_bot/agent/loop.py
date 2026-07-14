from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pixel_bot.agent.memory import AgentMemory
from pixel_bot.agent.models import AgentDecision
from pixel_bot.agent.workspace import Workspace
from pixel_bot.core.executor import execute_action
from pixel_bot.core.safety import Action, validate_action
from pixel_bot.vision.screen_capture import capture_screen


class DecisionProvider(Protocol):
    def decide(
