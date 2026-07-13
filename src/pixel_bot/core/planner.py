from dataclasses import dataclass, field
from typing import Any

from pixel_bot.core.command_parser import parse_command
from pixel_bot.core.safety import Action, validate_action


@dataclass
class PlanStep:
    id: int
    action: str
    parameters: dict[str, Any]
    status: str = "pending"


@dataclass
class Plan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "status": self.status,
            "steps": [
                {
                    "id": step.id,
                    "action": step.action,
                    "parameters": step.parameters,
                    "status": step.status,
                }
                for step in self.steps
            ],
        }


class Planner:
    def create_plan(self, goal: str) -> Plan:
        normalized_goal = goal.strip()

        if not normalized_goal:
            raise ValueError("L'obiettivo non può essere vuoto.")

        actions = parse_command(normalized_goal)

        steps = []

        for index, action in enumerate(actions, start=1):
            validate_action(action)

            steps.append(
                PlanStep(
                    id=index,
                    action=action.name,
                    parameters=action.parameters.copy(),
                )
            )

        return Plan(
            goal=normalized_goal,
            steps=steps,
            status="ready",
        )

    def plan_to_actions(self, plan: Plan) -> list[Action]:
        if plan.status not in {"ready", "running"}:
            raise ValueError(
                f"Il piano non è eseguibile. Stato corrente: {plan.status}"
            )

        actions = []

        for step in plan.steps:
            action = Action(
                name=step.action,
                parameters=step.parameters.copy(),
            )

            validate_action(action)
            actions.append(action)

        return actions