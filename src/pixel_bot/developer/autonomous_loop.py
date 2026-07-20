from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from .autonomous_planner import AutonomousPlanner, PlanStep
from .checklist_engine import Checklist
from .task_memory import PersistentTaskMemory, TaskRecord


@dataclass(slots=True)
class LoopResult:
    status: str
    rounds: int
    completed_steps: int
    reason: str = ""


class AutonomousVerificationLoop:
    def __init__(
        self,
        planner: AutonomousPlanner,
        memory: PersistentTaskMemory,
        executor: Callable[[PlanStep], Any],
        verifier: Callable[[PlanStep, Any], tuple[bool, str]],
        max_rounds: int = 20,
    ) -> None:
        self.planner = planner
        self.memory = memory
        self.executor = executor
        self.verifier = verifier
        self.max_rounds = max_rounds

    def run(self, task_id: str, goal: str, checklist: Checklist) -> LoopResult:
        record = self.memory.load() or TaskRecord(task_id=task_id, goal=goal)
        steps = self.planner.build(goal, [item.text for item in checklist.items])
        self.planner.validate(steps)

        for index, saved in enumerate(record.context.get("steps", [])):
            if index < len(steps):
                steps[index].status = saved.get("status", "pending")

        rounds = 0
        while rounds < self.max_rounds:
            step = self.planner.next_ready(steps)
            if step is None:
                complete = all(s.status == "completed" for s in steps)
                record.status = "completed" if complete else "blocked"
                record.context["steps"] = [self._step_dict(s) for s in steps]
                self.memory.save(record)
                return LoopResult(record.status, rounds, sum(s.status == "completed" for s in steps))

            step.status = "running"
            self.memory.append_event(record, "step_started", step_id=step.id, objective=step.objective)
            try:
                output = self.executor(step)
                ok, evidence = self.verifier(step, output)
            except Exception as exc:
                ok, evidence = False, str(exc)

            if ok:
                step.status = "completed"
                checklist.get(step.id).complete(evidence)
                self.memory.append_event(record, "step_completed", step_id=step.id, evidence=evidence)
            else:
                step.status = "failed"
                record.status = "failed"
                record.context["steps"] = [self._step_dict(s) for s in steps]
                self.memory.append_event(record, "step_failed", step_id=step.id, reason=evidence)
                return LoopResult("failed", rounds + 1, sum(s.status == "completed" for s in steps), evidence)

            record.current_step = step.id
            record.context["steps"] = [self._step_dict(s) for s in steps]
            self.memory.save(record)
            rounds += 1

        record.status = "bounded"
        self.memory.save(record)
        return LoopResult("bounded", rounds, sum(s.status == "completed" for s in steps), "max_rounds raggiunto")

    @staticmethod
    def _step_dict(step: PlanStep) -> dict:
        return {"id": step.id, "objective": step.objective, "depends_on": list(step.depends_on), "status": step.status}
