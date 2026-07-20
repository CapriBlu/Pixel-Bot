from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .autonomous_planner import AutonomousPlanner, PlanStep
from .checklist_engine import Checklist, ChecklistStatus
from .task_memory import PersistentTaskMemory, TaskRecord


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    delay_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts deve essere almeno 1")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds non può essere negativo")


@dataclass(slots=True)
class StepReport:
    step_id: int
    objective: str
    status: str
    attempts: int
    evidence: str = ""
    error: str = ""


@dataclass(slots=True)
class OrchestrationReport:
    task_id: str
    goal: str
    status: str
    started_at: str
    finished_at: str
    completed_steps: int
    total_steps: int
    resumed: bool
    steps: list[StepReport] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AutonomousOrchestrator:
    """Coordina piano, memoria, retry, verifica e report finale.

    L'orchestratore non decide autonomamente quali azioni desktop eseguire:
    riceve un executor e un verifier espliciti, mantenendo il confine di
    sicurezza del progetto.
    """

    def __init__(
        self,
        planner: AutonomousPlanner,
        memory: PersistentTaskMemory,
        executor: Callable[[PlanStep], Any],
        verifier: Callable[[PlanStep, Any], tuple[bool, str]],
        retry_policy: RetryPolicy | None = None,
        report_path: Path | None = None,
    ) -> None:
        self.planner = planner
        self.memory = memory
        self.executor = executor
        self.verifier = verifier
        self.retry_policy = retry_policy or RetryPolicy()
        self.report_path = report_path

    def run(self, task_id: str, goal: str, checklist: Checklist) -> OrchestrationReport:
        if not task_id.strip():
            raise ValueError("task_id non può essere vuoto")
        if not goal.strip():
            raise ValueError("goal non può essere vuoto")

        started_at = self._now()
        existing = self.memory.load()
        resumed = existing is not None
        if existing is not None and existing.task_id != task_id:
            raise ValueError(
                f"La memoria contiene il task '{existing.task_id}', non '{task_id}'. "
                "Usare una memoria dedicata o cancellarla prima di proseguire."
            )

        record = existing or TaskRecord(task_id=task_id, goal=goal)
        if existing is not None and existing.goal != goal:
            raise ValueError("Il goal non coincide con quello salvato nella memoria del task")

        steps = self.planner.build(goal, [item.text for item in checklist.items])
        self.planner.validate(steps)
        self._restore_state(record, steps, checklist)

        step_reports: list[StepReport] = []
        for step in steps:
            if step.status == "completed":
                previous = self._saved_step(record, step.id)
                step_reports.append(
                    StepReport(
                        step_id=step.id,
                        objective=step.objective,
                        status="completed",
                        attempts=int(previous.get("attempts", 0)),
                        evidence=str(previous.get("evidence", "ripristinato dalla memoria")),
                    )
                )
                continue

            report = self._execute_step(record, step, checklist)
            step_reports.append(report)
            self._persist_state(record, steps, step_reports)
            if report.status != "completed":
                record.status = "failed"
                self.memory.append_event(
                    record,
                    "task_failed",
                    step_id=step.id,
                    attempts=report.attempts,
                    reason=report.error or report.evidence,
                )
                return self._finish(record, started_at, resumed, steps, step_reports)

        record.status = "completed"
        record.current_step = steps[-1].id if steps else 0
        self._persist_state(record, steps, step_reports)
        self.memory.append_event(record, "task_completed", completed_steps=len(steps))
        return self._finish(record, started_at, resumed, steps, step_reports)

    def _execute_step(self, record: TaskRecord, step: PlanStep, checklist: Checklist) -> StepReport:
        item = checklist.get(step.id)
        item.mark_running()
        step.status = "running"
        last_error = ""
        last_evidence = ""

        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.memory.append_event(
                record,
                "step_attempt_started",
                step_id=step.id,
                objective=step.objective,
                attempt=attempt,
            )
            try:
                output = self.executor(step)
                ok, evidence = self.verifier(step, output)
                last_evidence = str(evidence or "")
                if ok:
                    step.status = "completed"
                    item.complete(last_evidence)
                    record.current_step = step.id
                    self.memory.append_event(
                        record,
                        "step_completed",
                        step_id=step.id,
                        attempt=attempt,
                        evidence=last_evidence,
                    )
                    return StepReport(
                        step_id=step.id,
                        objective=step.objective,
                        status="completed",
                        attempts=attempt,
                        evidence=last_evidence,
                    )
                last_error = last_evidence or "verifica non superata"
            except Exception as exc:  # il confine registra l'errore senza nasconderlo
                last_error = f"{type(exc).__name__}: {exc}"

            self.memory.append_event(
                record,
                "step_attempt_failed",
                step_id=step.id,
                attempt=attempt,
                reason=last_error,
            )
            if attempt < self.retry_policy.max_attempts and self.retry_policy.delay_seconds:
                time.sleep(self.retry_policy.delay_seconds)

        step.status = "failed"
        item.status = ChecklistStatus.PENDING
        return StepReport(
            step_id=step.id,
            objective=step.objective,
            status="failed",
            attempts=self.retry_policy.max_attempts,
            evidence=last_evidence,
            error=last_error,
        )

    def _restore_state(self, record: TaskRecord, steps: list[PlanStep], checklist: Checklist) -> None:
        saved_steps = {int(item["id"]): item for item in record.context.get("steps", []) if "id" in item}
        for step in steps:
            saved = saved_steps.get(step.id)
            if not saved:
                continue
            step.status = str(saved.get("status", "pending"))
            if step.status == "completed":
                checklist.get(step.id).complete(str(saved.get("evidence", "ripristinato dalla memoria")))

    def _persist_state(
        self,
        record: TaskRecord,
        steps: list[PlanStep],
        reports: list[StepReport],
    ) -> None:
        by_id = {report.step_id: report for report in reports}
        record.context["steps"] = []
        for step in steps:
            report = by_id.get(step.id)
            record.context["steps"].append(
                {
                    "id": step.id,
                    "objective": step.objective,
                    "depends_on": list(step.depends_on),
                    "status": step.status,
                    "attempts": report.attempts if report else 0,
                    "evidence": report.evidence if report else "",
                    "error": report.error if report else "",
                }
            )
        self.memory.save(record)

    def _finish(
        self,
        record: TaskRecord,
        started_at: str,
        resumed: bool,
        steps: list[PlanStep],
        reports: list[StepReport],
    ) -> OrchestrationReport:
        report = OrchestrationReport(
            task_id=record.task_id,
            goal=record.goal,
            status=record.status,
            started_at=started_at,
            finished_at=self._now(),
            completed_steps=sum(step.status == "completed" for step in steps),
            total_steps=len(steps),
            resumed=resumed,
            steps=reports,
        )
        if self.report_path is not None:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.report_path.with_suffix(self.report_path.suffix + ".tmp")
            tmp.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.report_path)
        return report

    @staticmethod
    def _saved_step(record: TaskRecord, step_id: int) -> dict[str, Any]:
        for item in record.context.get("steps", []):
            if int(item.get("id", -1)) == step_id:
                return item
        return {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
