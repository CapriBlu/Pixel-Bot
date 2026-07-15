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

from pixel_bot.agent.budget import BudgetState
from pixel_bot.agent.models import AgentDecision
from pixel_bot.agent.workspace import Workspace

Transport = Callable[[Request, float], dict[str, Any]]


@dataclass(slots=True)
class AIClientConfig:
    endpoint: str = ""
    token: str | None = None
    model: str = "gpt-5-mini"
    provider: str = "custom"
    timeout_seconds: float = 45.0
    max_history_items: int = 12
    max_requests_per_task: int = 10
    estimated_cost_per_request: float = 0.01
    max_estimated_cost: float = 0.10
    max_retry_attempts: int = 3
    retry_backoff_seconds: float = 1.0
    dry_run: bool = False

    @classmethod
    def from_environment(cls) -> "AIClientConfig":
        dry_run = os.getenv("PIXEL_BOT_DRY_RUN", "0") == "1"
        openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        endpoint = os.getenv("PIXEL_BOT_AI_ENDPOINT", "").strip()
        provider = (os.getenv("PIXEL_BOT_AI_PROVIDER") or "").strip().lower()

        if not endpoint and openai_key:
            endpoint = "https://api.openai.com/v1/responses"
            provider = "openai"
        elif endpoint and "api.openai.com/v1/responses" in endpoint:
            provider = "openai"
        elif not provider:
            provider = "custom"

        if not endpoint and not dry_run:
            raise RuntimeError("Configurare OPENAI_API_KEY oppure PIXEL_BOT_AI_ENDPOINT.")

        token = os.getenv("PIXEL_BOT_AI_TOKEN") or openai_key or None
        if provider == "openai" and not token and not dry_run:
            raise RuntimeError("OPENAI_API_KEY non configurata.")

        return cls(
            endpoint=endpoint,
            token=token,
            model=(os.getenv("OPENAI_MODEL") or "gpt-5-mini").strip(),
            provider=provider,
            timeout_seconds=float(os.getenv("PIXEL_BOT_AI_TIMEOUT", "45")),
            max_history_items=int(os.getenv("PIXEL_BOT_MAX_HISTORY", "12")),
            max_requests_per_task=int(os.getenv("PIXEL_BOT_MAX_REQUESTS", "10")),
            estimated_cost_per_request=float(
                os.getenv("PIXEL_BOT_ESTIMATED_COST_PER_REQUEST", "0.01")
            ),
            max_estimated_cost=float(os.getenv("PIXEL_BOT_MAX_ESTIMATED_COST", "0.10")),
            max_retry_attempts=max(1, int(os.getenv("PIXEL_BOT_AI_MAX_RETRIES", "3"))),
            retry_backoff_seconds=max(0.0, float(os.getenv("PIXEL_BOT_AI_RETRY_BACKOFF", "1.0"))),
            dry_run=dry_run,
        )



@dataclass(slots=True)
class AIClient:
    config: AIClientConfig
    workspace: Workspace | None = None
    transport: Transport | None = None
    simulated_decisions: Iterable[AgentDecision] | None = None
    budget: BudgetState = field(init=False)
    _simulation_iterator: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        if self.config.max_requests_per_task <= 0:
            raise ValueError("max_requests_per_task deve essere maggiore di zero.")
        self.budget = BudgetState(
            max_requests=self.config.max_requests_per_task,
            max_estimated_cost=self.config.max_estimated_cost,
            estimated_cost_per_request=self.config.estimated_cost_per_request,
        )
        if self.simulated_decisions is not None:
            self._simulation_iterator = iter(self.simulated_decisions)

    @property
    def request_count(self) -> int:
        return self.budget.requests_used

    def decide(
        self,
        *,
        goal: str,
        screenshot_path: Path,
        history: list[dict[str, Any]],
    ) -> AgentDecision:
        self.budget.ensure_available()

        if self.config.dry_run:
            decision = self._next_simulated_decision()
            self.budget.record_request()
            self._record_usage("simulation")
            return decision

        if not self.config.endpoint:
            raise RuntimeError("Endpoint AI non configurato.")
        if not screenshot_path.is_file():
            raise FileNotFoundError(f"Screenshot non trovato: {screenshot_path}")

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
        response_payload = self._send(request)
        decision_payload = response_payload.get("decision", response_payload)
        if not isinstance(decision_payload, dict):
            raise RuntimeError("La risposta AI non contiene una decisione valida.")

        decision = AgentDecision.from_dict(decision_payload)
        self.budget.record_request()
        self._record_usage("remote")
        return decision

    def _next_simulated_decision(self) -> AgentDecision:
        if self._simulation_iterator is None:
            return AgentDecision(
                observation="Modalità simulazione attiva.",
                reasoning_summary="Nessuna chiamata remota eseguita.",
                completed=True,
            )
        try:
            return next(self._simulation_iterator)
        except StopIteration as error:
            raise RuntimeError("Decisioni simulate esaurite.") from error

    def _send(self, request: Request) -> dict[str, Any]:
        if self.transport is not None:
            payload = self.transport(request, self.config.timeout_seconds)
            if not isinstance(payload, dict):
                raise RuntimeError("Il transport AI deve restituire un oggetto JSON.")
            return payload
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Backend AI HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Backend AI non raggiungibile: {error.reason}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError("Il backend AI ha restituito JSON non valido.") from error
        if not isinstance(payload, dict):
            raise RuntimeError("Il backend AI deve restituire un oggetto JSON.")
        return payload

    def _record_usage(self, mode: str) -> None:
        if self.workspace is not None:
            self.workspace.append_event(
                "ai_request",
                {"mode": mode, "budget": self.budget.to_dict()},
            )
