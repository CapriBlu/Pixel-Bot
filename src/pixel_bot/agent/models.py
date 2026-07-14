from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pixel_bot.core.safety import Action


@dataclass(slots=True)
class AgentDecision:
    observation: str
    reasoning_summary: str
    completed: bool
    action_name: str | None = None
    action_parameters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentDecision":
        action = payload.get("action")
        action_name: str | None = None
        action_parameters: dict[str, Any] = {}

        if action is not None:
            if not isinstance(action, dict):
                raise ValueError("Il campo action deve essere un oggetto o null.")

            action_name = action.get("name")
            action_parameters = action.get("parameters", {})

            if not isinstance(action_name, str) or not action_name:
                raise ValueError("Il nome dell'azione AI non è valido.")

            if not isinstance(action_parameters, dict):
                raise ValueError("I parametri dell'azione AI non sono validi.")

        completed = payload.get("completed", False)
        if not isinstance(completed, bool):
            raise ValueError("Il campo completed deve essere booleano.")

        if completed and action is not None:
            raise ValueError("Una decisione completata non può contenere un'azione.")

        if not completed and action is None:
            raise ValueError("Una decisione non completata deve contenere un'azione.")

        return cls(
            observation=str(payload.get("observation", "")),
            reasoning_summary=str(payload.get("reasoning_summary", "")),
            completed=completed,
            action_name=action_name,
            action_parameters=action_parameters,
        )

    def to_action(self) -> Action:
        if self.completed or self.action_name is None:
            raise ValueError("La decisione non contiene un'azione eseguibile.")

        return Action(
            name=self.action_name,
            parameters=self.action_parameters.copy(),
        )

    def to_dict(self) -> dict[str, Any]:
        action: dict[str, Any] | None = None
        if self.action_name is not None:
            action = {
                "name": self.action_name,
                "parameters": self.action_parameters.copy(),
            }

        return {
            "observation": self.observation,
            "reasoning_summary": self.reasoning_summary,
            "completed": self.completed,
            "action": action,
        }
