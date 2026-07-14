from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pixel_bot.agent.models import AgentDecision
from pixel_bot.agent.workspace import Workspace

Transport = Callable[[Request, float], dict[str, Any]]


@dataclass(slots=True)
class AIClientConfig:
    endpoint: str = ""
    token: str | None = None
    timeout_seconds: float = 45.0
    max_history_items: int = 12
    max_requests_per_task: int = 10
    estimated_cost_per_request: float = 0.01
    max_estimated_cost: float = 0.10
    dry_run: bool = False

    @classmethod
    def from_environment(cls) -> "AIClientConfig":
        dry_run = os.getenv("PIXEL_BOT_DRY_RUN", "0") == "1"
        endpoint = os.getenv("PIXEL_BOT_AI_ENDPOINT", "").strip()
        if not endpoint and not dry_run:
            raise RuntimeError("PIXEL_BOT_AI_ENDPOINT