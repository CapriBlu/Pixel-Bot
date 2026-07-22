from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .state_collector import StateCollector
from .state_sanitizer import sanitize_state
from .state_tools import SafeToolRegistry


class OpenAIStateBridge:
    def __init__(self, repository_root: Path, model: str | None = None) -> None:
        self.root = repository_root.resolve()
        self.model = model or os.getenv("PIXEL_OPENAI_MODEL", "gpt-5")
        self.registry = SafeToolRegistry(self.root)

    def analyze(self, goal: str, max_rounds: int = 6) -> dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Installare il pacchetto openai nella .venv"
            ) from exc

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY non configurata")

        state = sanitize_state(
            StateCollector(self.root).collect(goal)
        )

        client = OpenAI()

        instructions = (
            "Sei il cervello tecnico di Pixel Bot. "
            "Analizza lo stato locale strutturato. "
            "Usa solo gli strumenti sicuri disponibili per ottenere "
            "i dettagli mancanti. "
            "Non chiedere all'utente informazioni recuperabili dagli strumenti. "
            "Non proporre comandi distruttivi. "
            "Alla fine restituisci una spiegazione concreta, "
            "la classificazione VERDE/ARANCIONE/ROSSO "
            "e le azioni successive."
        )

        conversation: list[Any] = [
            {
                "role": "user",
                "content": json.dumps(
                    state,
                    ensure_ascii=False,
                ),
            }
        ]

        rounds = 0
        response = None

        while rounds < max_rounds:
            response = client.responses.create(
                model=self.model,
                instructions=instructions,
                input=conversation,
                tools=self.registry.schemas,
                store=False,
            )

            calls = [
                item
                for item in response.output
                if getattr(item, "type", None) == "function_call"
            ]

            if not calls:
                return {
                    "status": "completed",
                    "response_id": response.id,
                    "request_id": getattr(
                        response,
                        "_request_id",
                        None,
                    ),
                    "text": response.output_text,
                    "rounds": rounds,
                }

            conversation.extend(response.output)

            for call in calls:
                try:
                    arguments = json.loads(
                        call.arguments or "{}"
                    )
                except json.JSONDecodeError:
                    arguments = {}

                try:
                    result = self.registry.execute(
                        call.name,
                        arguments,
                    )
                except Exception as exc:
                    result = {
                        "ok": False,
                        "error": str(exc),
                        "tool": call.name,
                    }

                conversation.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(
                            sanitize_state(result),
                            ensure_ascii=False,
                        ),
                    }
                )

            rounds += 1

        return {
            "status": "bounded",
            "response_id": response.id if response else None,
            "text": response.output_text if response else "",
            "rounds": rounds,
        }
