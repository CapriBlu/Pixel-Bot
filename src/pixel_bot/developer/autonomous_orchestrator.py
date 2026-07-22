from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .autonomous_planner import AutonomousPlanner, PlanStep
from .checklist_engine import Checklist, ChecklistStatus
from .checkpoint_manager import CheckpointManager
from .loop_watchdog import LoopWatchdog, WatchdogTimeout
from .recovery_manager import RecoveryManager
from .reliability_metrics import ReliabilityMetrics
from .loop_state import LoopStatus, StepStatus, coerce_step_status
from .task_memory import PersistentTaskMemory, TaskRecord
from .event_bus import EventBus


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
    error_type: str = ""


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
    rounds: int = 0
    steps: list[StepReport] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AutonomousOrchestrator:
    """Motore canonico dell'auto-loop: piano, memoria, retry e verifica."""

    def __init__(
        self,
        planner: AutonomousPlanner,
        memory: PersistentTaskMemory,
        executor: Callable[[PlanStep], Any],
        verifier: Callable[[PlanStep, Any], tuple[bool, str]],
        retry_policy: RetryPolicy | None = None,
        report_path: Path | None = None,
        max_rounds: int = 20,
        checkpoint_manager: CheckpointManager | None = None,
        watchdog: LoopWatchdog | None = None,
        metrics: ReliabilityMetrics | None = None,
        recovery_manager: RecoveryManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        if max_rounds < 1:
            raise ValueError("max_rounds deve essere almeno 1")
        self.planner = planner
        self.memory = memory
        self.executor = executor
        self.verifier = verifier
        self.retry_policy = retry_policy or RetryPolicy()
        self.report_path = report_path
        self.max_rounds = max_rounds
        self.checkpoint_manager = checkpoint_manager
        self.watchdog = watchdog
        self.metrics = metrics or ReliabilityMetrics()
        self.recovery_manager = recovery_manager or RecoveryManager()
        self.event_bus = event_bus

    def run(self, task_id: str, goal: str, checklist: Checklist) -> OrchestrationReport:
        if not task_id.strip():
            raise ValueError("task_id non può essere vuoto")
        if not goal.strip():
            raise ValueError("goal non può essere vuoto")

        started_at = self._now()
        existing = self.memory.load()
        checkpoint_restored = False
        if existing is None and self.checkpoint_manager is not None:
            candidate = self.checkpoint_manager.restore_record()
            if candidate is not None and candidate.task_id == task_id and candidate.goal == goal:
                existing = candidate
                self.memory.save(candidate)
                checkpoint_restored = True
        resumed = existing is not None
        self.metrics.increment("tasks_started")
        self._emit("task_started", task_id=task_id, goal=goal, resumed=resumed)
        if resumed:
            self.metrics.increment("resumes")
        if existing is not None and existing.task_id != task_id:
            raise ValueError(
                f"La memoria contiene il task '{existing.task_id}', non '{task_id}'. "
                "Usare una memoria dedicata o cancellarla prima di proseguire."
            )

        record = existing or TaskRecord(task_id=task_id, goal=goal)
        if existing is not None and existing.goal != goal:
            raise ValueError("Il goal non coincide con quello salvato nella memoria del task")

        self._transition(record, LoopStatus.PLANNING, "planning_started")
        steps = self.planner.build(goal, [item.text for item in checklist.items])
        self.planner.validate(steps)
        self._restore_state(record, steps, checklist)
        self._checkpoint(record, "planning_completed")
        if checkpoint_restored:
            self.memory.append_event(record, "checkpoint_restored")

        step_reports: list[StepReport] = []
        rounds = int(record.context.get("rounds", 0))
        for step in steps:
            if step.status == StepStatus.COMPLETED:
                previous = self._saved_step(record, step.id)
                step_reports.append(
                    StepReport(
                        step_id=step.id,
                        objective=step.objective,
                        status=StepStatus.COMPLETED,
                        attempts=int(previous.get("attempts", 0)),
                        evidence=str(previous.get("evidence", "ripristinato dalla memoria")),
                    )
                )
                continue

            report, rounds = self._execute_step(record, step, checklist, steps, step_reports, rounds)
            step_reports.append(report)
            self._persist_state(record, steps, step_reports, rounds)
            if report.status != StepStatus.COMPLETED:
                if record.status != LoopStatus.BOUNDED:
                    self._transition(
                        record,
                        LoopStatus.FAILED,
                        "task_failed",
                        step_id=step.id,
                        attempts=report.attempts,
                        reason=report.error or report.evidence,
                        error_type=report.error_type,
                    )
                return self._finish(record, started_at, resumed, steps, step_reports, rounds)

        record.current_step = steps[-1].id if steps else 0
        self._persist_state(record, steps, step_reports, rounds)
        self._transition(record, LoopStatus.COMPLETED, "task_completed", completed_steps=len(steps))
        return self._finish(record, started_at, resumed, steps, step_reports, rounds)

    def _execute_step(
        self,
        record: TaskRecord,
        step: PlanStep,
        checklist: Checklist,
        steps: list[PlanStep],
        reports: list[StepReport],
        rounds: int,
    ) -> tuple[StepReport, int]:
        item = checklist.get(step.id)
        item.mark_running()
        step.status = StepStatus.RUNNING
        last_error = ""
        last_evidence = ""
        last_error_type = ""
        saved_attempts = int(self._saved_step(record, step.id).get("attempts", 0))

        for attempt in range(saved_attempts + 1, self.retry_policy.max_attempts + 1):
            if rounds >= self.max_rounds:
                step.status = StepStatus.FAILED
                self._persist_state(record, steps, reports, rounds)
                self._transition(
                    record,
                    LoopStatus.BOUNDED,
                    "round_limit_reached",
                    step_id=step.id,
                    max_rounds=self.max_rounds,
                )
                return StepReport(
                    step_id=step.id,
                    objective=step.objective,
                    status=StepStatus.FAILED,
                    attempts=attempt - 1,
                    error="max_rounds raggiunto",
                    error_type="round_limit_reached",
                ), rounds

            rounds += 1
            self._transition(
                record,
                LoopStatus.RUNNING,
                "step_attempt_started",
                step_id=step.id,
                objective=step.objective,
                attempt=attempt,
                rounds=rounds,
            )
            step.status = StepStatus.RUNNING
            self._persist_state(record, steps, reports, rounds, active_step=step, active_attempt=attempt)

            step_started = time.monotonic()
            try:
                if self.watchdog is not None:
                    self.watchdog.check()
                    self.watchdog.touch(step_id=step.id, phase="executing")
                output = self.executor(step)
                if self.watchdog is not None:
                    self.watchdog.check()
                    self.watchdog.touch(step_id=step.id, phase="executed")
            except WatchdogTimeout as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                last_error_type = "watchdog_timeout"
                self.metrics.increment("watchdog_interventions")
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                last_error_type = "execution_error"
                self.metrics.increment("execution_failures")
            else:
                step.status = StepStatus.VERIFYING
                self._transition(
                    record,
                    LoopStatus.VERIFYING,
                    "step_verification_started",
                    step_id=step.id,
                    attempt=attempt,
                )
                self._persist_state(record, steps, reports, rounds, active_step=step, active_attempt=attempt)
                try:
                    if self.watchdog is not None:
                        self.watchdog.touch(step_id=step.id, phase="verifying")
                    verification = self.verifier(step, output)
                    if self.watchdog is not None:
                        self.watchdog.check()
                        self.watchdog.touch(step_id=step.id, phase="verified")
                    if not isinstance(verification, tuple) or len(verification) != 2:
                        raise TypeError("Il verifier deve restituire una tupla (bool, evidence)")
                    ok, evidence = verification
                    if not isinstance(ok, bool):
                        raise TypeError("Il primo valore restituito dal verifier deve essere bool")
                    last_evidence = str(evidence or "")
                except WatchdogTimeout as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    last_error_type = "watchdog_timeout"
                    self.metrics.increment("watchdog_interventions")
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    last_error_type = "verification_error"
                    self.metrics.increment("verification_errors")
                else:
                    if ok:
                        step.status = StepStatus.COMPLETED
                        self.metrics.increment("steps_completed")
                        self.metrics.record_step_duration(time.monotonic() - step_started)
                        item.complete(last_evidence)
                        record.current_step = step.id
                        self.memory.append_event(
                            record,
                            "step_completed",
                            step_id=step.id,
                            attempt=attempt,
                            evidence=last_evidence,
                            rounds=rounds,
                        )
                        return StepReport(
                            step_id=step.id,
                            objective=step.objective,
                            status=StepStatus.COMPLETED,
                            attempts=attempt,
                            evidence=last_evidence,
                        ), rounds
                    last_error = last_evidence or "verifica non superata"
                    last_error_type = "verification_failed"
                    self.metrics.increment("verification_failures")

            self.memory.append_event(
                record,
                "step_attempt_failed",
                step_id=step.id,
                attempt=attempt,
                reason=last_error,
                error_type=last_error_type,
                rounds=rounds,
            )
            decision = self.recovery_manager.decide(
                last_error_type, attempt, self.retry_policy.max_attempts
            )
            self.memory.append_event(
                record,
                "recovery_decision",
                step_id=step.id,
                attempt=attempt,
                action=str(decision.action),
                reason=decision.reason,
            )
            if attempt < self.retry_policy.max_attempts:
                self.metrics.increment("retries")
                step.status = StepStatus.RETRYING
                self._transition(
                    record,
                    LoopStatus.RETRYING,
                    "step_retry_scheduled",
                    step_id=step.id,
                    attempt=attempt,
                    next_attempt=attempt + 1,
                    reason=last_error,
                    error_type=last_error_type,
                )
                self._persist_state(record, steps, reports, rounds, active_step=step, active_attempt=attempt)
                if self.retry_policy.delay_seconds:
                    time.sleep(self.retry_policy.delay_seconds)

        step.status = StepStatus.FAILED
        item.status = ChecklistStatus.PENDING
        return StepReport(
            step_id=step.id,
            objective=step.objective,
            status=StepStatus.FAILED,
            attempts=self.retry_policy.max_attempts,
            evidence=last_evidence,
            error=last_error,
            error_type=last_error_type or "retry_limit_reached",
        ), rounds

    def _restore_state(self, record: TaskRecord, steps: list[PlanStep], checklist: Checklist) -> None:
        saved_steps = {int(item["id"]): item for item in record.context.get("steps", []) if "id" in item}
        for step in steps:
            saved = saved_steps.get(step.id)
            if not saved:
                continue
            saved_status = coerce_step_status(str(saved.get("status", StepStatus.PENDING)))
            if saved_status == StepStatus.COMPLETED:
                step.status = StepStatus.COMPLETED
                checklist.get(step.id).complete(str(saved.get("evidence", "ripristinato dalla memoria")))
            else:
                step.status = StepStatus.PENDING

    def _persist_state(
        self,
        record: TaskRecord,
        steps: list[PlanStep],
        reports: list[StepReport],
        rounds: int,
        active_step: PlanStep | None = None,
        active_attempt: int | None = None,
    ) -> None:
        by_id = {report.step_id: report for report in reports}
        previous = {int(item.get("id", -1)): item for item in record.context.get("steps", [])}
        record.context["steps"] = []
        for step in steps:
            report = by_id.get(step.id)
            old = previous.get(step.id, {})
            attempts = report.attempts if report else int(old.get("attempts", 0))
            if active_step is not None and step.id == active_step.id and active_attempt is not None:
                attempts = active_attempt
            record.context["steps"].append(
                {
                    "id": step.id,
                    "objective": step.objective,
                    "depends_on": list(step.depends_on),
                    "status": str(step.status),
                    "attempts": attempts,
                    "evidence": report.evidence if report else str(old.get("evidence", "")),
                    "error": report.error if report else str(old.get("error", "")),
                    "error_type": report.error_type if report else str(old.get("error_type", "")),
                }
            )
        record.context["rounds"] = rounds
        record.context["total_attempts"] = rounds
        self.memory.save(record)
        self._checkpoint(
            record,
            "state_persisted",
            active_step=active_step.id if active_step is not None else None,
            active_attempt=active_attempt,
        )

    def _checkpoint(
        self,
        record: TaskRecord,
        reason: str,
        *,
        active_step: int | None = None,
        active_attempt: int | None = None,
    ) -> None:
        if self.checkpoint_manager is not None:
            self.checkpoint_manager.save(
                record,
                reason,
                active_step=active_step,
                active_attempt=active_attempt,
            )

    def _transition(self, record: TaskRecord, status: LoopStatus, event: str, **payload: Any) -> None:
        previous = str(record.status)
        record.status = status
        record.context["last_transition"] = f"{previous} -> {status}"
        if "error_type" in payload:
            record.context["last_error_type"] = payload["error_type"]
        self.memory.append_event(record, event, status=str(status), previous_status=previous, **payload)
        self._emit(event, task_id=record.task_id, status=str(status), previous_status=previous, **payload)

    def _finish(
        self,
        record: TaskRecord,
        started_at: str,
        resumed: bool,
        steps: list[PlanStep],
        reports: list[StepReport],
        rounds: int,
    ) -> OrchestrationReport:
        if str(record.status) == str(LoopStatus.COMPLETED):
            self.metrics.increment("tasks_completed")
        else:
            self.metrics.increment("tasks_failed")
        self._checkpoint(record, "task_finished")
        report = OrchestrationReport(
            task_id=record.task_id,
            goal=record.goal,
            status=str(record.status),
            started_at=started_at,
            finished_at=self._now(),
            completed_steps=sum(step.status == StepStatus.COMPLETED for step in steps),
            total_steps=len(steps),
            resumed=resumed,
            rounds=rounds,
            steps=reports,
        )
        if self.report_path is not None:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.report_path.with_suffix(self.report_path.suffix + ".tmp")
            tmp.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.report_path)
        self._emit("task_finished", task_id=record.task_id, status=str(record.status), rounds=rounds, completed_steps=report.completed_steps, total_steps=report.total_steps)
        return report

    def _emit(self, event_type: str, **payload: Any) -> None:
        if self.event_bus is not None:
            self.event_bus.publish(event_type, payload)

    @staticmethod
    def _saved_step(record: TaskRecord, step_id: int) -> dict[str, Any]:
        for item in record.context.get("steps", []):
            if int(item.get("id", -1)) == step_id:
                return item
        return {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
