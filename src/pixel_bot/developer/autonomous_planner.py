from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(slots=True)
class PlanStep:
    id: int
    objective: str
    depends_on: tuple[int, ...] = ()
    status: str = "pending"
    metadata: dict = field(default_factory=dict)


class AutonomousPlanner:
    """Planner deterministico di base, estendibile con un provider AI."""

    def build(self, goal: str, checklist_items: Iterable[str]) -> list[PlanStep]:
        items = [item.strip() for item in checklist_items if item.strip()]
        if not items:
            items = [goal.strip()]
        steps: list[PlanStep] = []
        previous: int | None = None
        for index, item in enumerate(items, start=1):
            dependencies = () if previous is None else (previous,)
            steps.append(PlanStep(id=index, objective=item, depends_on=dependencies))
            previous = index
        return steps

    def next_ready(self, steps: list[PlanStep]) -> PlanStep | None:
        completed = {step.id for step in steps if step.status == "completed"}
        for step in steps:
            if step.status == "pending" and all(dep in completed for dep in step.depends_on):
                return step
        return None

    def validate(self, steps: list[PlanStep]) -> None:
        ids = [step.id for step in steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Gli ID dei passaggi devono essere univoci")
        known = set(ids)
        for step in steps:
            if step.id in step.depends_on:
                raise ValueError("Un passaggio non può dipendere da se stesso")
            missing = set(step.depends_on) - known
            if missing:
                raise ValueError(f"Dipendenze mancanti: {sorted(missing)}")
