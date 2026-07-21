from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .autonomous_orchestrator import AutonomousOrchestrator, RetryPolicy
from .autonomous_planner import AutonomousPlanner, PlanStep
from .checklist_engine import Checklist
from .task_memory import PersistentTaskMemory


@dataclass(slots=True)
class LoopResult:
    status: str
    rounds: int
    completed_steps: int
    reason: str = ""


class AutonomousVerificationLoop:
    """Adattatore compatibile verso l'AutonomousOrchestrator canonico."""

    def __init__(
        self,
        planner: AutonomousPlanner,
        memory: PersistentTaskMemory,
        executor: Callable[[PlanStep], Any],
        verifier: Callable[[PlanStep, Any], tuple[bool, str]],
        max_rounds: int = 20,
    ) -> None:
        self._orchestrator = AutonomousOrchestrator(
            planner=planner,
            memory=memory,
            executor=executor,
            verifier=verifier,
            retry_policy=RetryPolicy(max_attempts=1),
            max_rounds=max_rounds,
        )

    @property
    def planner(self) -> AutonomousPlanner:
        return self._orchestrator.planner

    @property
    def memory(self) -> PersistentTaskMemory:
        return self._orchestrator.memory

    @property
    def executor(self) -> Callable[[PlanStep], Any]:
        return self._orchestrator.executor

    @property
    def verifier(self) -> Callable[[PlanStep, Any], tuple[bool, str]]:
        return self._orchestrator.verifier

    @property
    def max_rounds(self) -> int:
        return self._orchestrator.max_rounds

    def run(self, task_id: str, goal: str, checklist: Checklist) -> LoopResult:
        report = self._orchestrator.run(task_id, goal, checklist)
        reason = ""
        if report.steps and report.status != "completed":
            last = report.steps[-1]
            reason = last.error or last.evidence
        if report.status == "bounded" and not reason:
            reason = "max_rounds raggiunto"
        return LoopResult(
            status=report.status,
            rounds=report.rounds,
            completed_steps=report.completed_steps,
            reason=reason,
        )
