from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pixel_bot.agent.models import AgentDecision


@dataclass(slots=True)
class AIClientConfig:
    endpoint: str
    token: str | None = None
    timeout_seconds: float = 45.0
    max_history_items: int = 12
    dry_run: bool = False

    @classmethod
    def from_environment(cls) -> "AIClientConfig":
        endpoint = os.getenv("PIXEL_BOT_AI_ENDPOINT", "").strip()
        if not endpoint:
            raise RuntimeError("PIXEL_BOT_AI_ENDPOINT non configurato.")
        return cls(
            endpoint=endpoint,
            token=os.getenv("PIXEL_BOT_AI_TOKEN"),
            timeout_seconds=float(os.getenv("PIXEL_BOT_AI_TIMEOUT", "45")),
            max_history_items=int(os.getenv("PIXEL_BOT_MAX_HISTORY", "12")),
            dry_run=os.getenv("PIXEL_BOT_DRY_RUN", "0") == "1",
        )


class AIClient:
    def __init__(self, config: AIClientConfig) -> None:
        self.config = config
        self.request_count = 0

    def decide(
        self,
        *,
        goal: str,
        screenshot_path: Path,
        history: list[dict[str, Any]],
    ) -> AgentDecision:
        if self.config.dry_run:
            return AgentDecision(
                observation="Modalità simulazione attiva.",
                reasoning_summary="Nessuna chiamata remota eseguita.",
                completed=True,
            )

        image_bytes = screenshot_path.read_bytes()
        payload = {
            "goal": goal,
            "screenshot": base64.b64encode(image_bytes).decode("ascii"),
            "screenshot_mime_type": "image/png",
            "history": history[-self.config.max_history_items :],
            "response_format": "agent_decision_v1",
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        request = Request(
            self.config.endpoint,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Backend AI HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Backend AI non raggiungibile: {error.reason}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError("Il backend AI ha restituito JSON non valido.") from error

        self.request_count += 1
        decision_payload = response_payload.get("decision", response_payload)
        if not isinstance(decision_payload, dict):
            raise RuntimeError("La risposta AI non contiene una decisione valida.")
        return AgentDecision.from_dict(decision_payload)
