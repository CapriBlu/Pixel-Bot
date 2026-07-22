from __future__ import annotations

import json

from pixel_bot.developer.autonomous_orchestrator import AutonomousOrchestrator, RetryPolicy
from pixel_bot.developer.autonomous_planner import AutonomousPlanner
from pixel_bot.developer.checklist_engine import Checklist
from pixel_bot.developer.checkpoint_manager import CheckpointManager
from pixel_bot.developer.loop_watchdog import LoopWatchdog, WatchdogTimeout
from pixel_bot.developer.recovery_manager import RecoveryAction, RecoveryManager
from pixel_bot.developer.reliability_metrics import ReliabilityMetrics
from pixel_bot.developer.task_memory import PersistentTaskMemory, TaskRecord


def test_checkpoint_roundtrip(tmp_path):
    manager = CheckpointManager(tmp_path / "checkpoint.json")
    record = TaskRecord(task_id="t1", goal="goal", status="running")
    record.context["rounds"] = 2
    manager.save(record, "test", active_step=1, active_attempt=2)

    restored = manager.restore_record()

    assert restored is not None
    assert restored.task_id == "t1"
    assert restored.context["rounds"] == 2
    assert manager.load().active_attempt == 2


def test_checkpoint_resume_without_memory_file(tmp_path):
    memory = PersistentTaskMemory(tmp_path / "memory.json")
    checkpoint = CheckpointManager(tmp_path / "checkpoint.json")
    record = TaskRecord(task_id="t1", goal="goal", status="retrying")
    record.context["rounds"] = 1
    record.context["steps"] = [
        {"id": 1, "objective": "Esegui", "depends_on": [], "status": "retrying", "attempts": 1}
    ]
    checkpoint.save(record, "simulated_crash", active_step=1, active_attempt=1)
    calls = []
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=memory,
        executor=lambda step: calls.append(step.id) or "ok",
        verifier=lambda step, output: (True, "done"),
        retry_policy=RetryPolicy(max_attempts=3),
        checkpoint_manager=checkpoint,
    )

    report = orchestrator.run("t1", "goal", Checklist.from_text("1. Esegui"))

    assert report.resumed is True
    assert report.status == "completed"
    assert report.steps[0].attempts == 2
    assert calls == [1]


def test_watchdog_detects_stall():
    now = [0.0]
    watchdog = LoopWatchdog(timeout_seconds=5, clock=lambda: now[0])
    watchdog.touch(step_id=3, phase="executing")
    now[0] = 6.0

    try:
        watchdog.check()
    except WatchdogTimeout as exc:
        assert "step=3" in str(exc)
    else:
        raise AssertionError("watchdog timeout atteso")


def test_orchestrator_classifies_watchdog_timeout(tmp_path):
    now = [0.0]
    watchdog = LoopWatchdog(timeout_seconds=1, clock=lambda: now[0])

    def executor(step):
        now[0] = 2.0
        return "late"

    metrics = ReliabilityMetrics(tmp_path / "metrics.json")
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "memory.json"),
        executor=executor,
        verifier=lambda step, output: (True, "ok"),
        retry_policy=RetryPolicy(max_attempts=1),
        watchdog=watchdog,
        metrics=metrics,
    )

    report = orchestrator.run("t1", "goal", Checklist.from_text("1. Esegui"))

    assert report.status == "failed"
    assert report.steps[0].error_type == "watchdog_timeout"
    assert metrics.snapshot.watchdog_interventions == 1


def test_metrics_persist_success_and_duration(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    metrics = ReliabilityMetrics(metrics_path)
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "memory.json"),
        executor=lambda step: "ok",
        verifier=lambda step, output: (True, "verified"),
        metrics=metrics,
    )

    report = orchestrator.run("t1", "goal", Checklist.from_text("1. Esegui"))
    saved = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert report.status == "completed"
    assert saved["tasks_started"] == 1
    assert saved["tasks_completed"] == 1
    assert saved["steps_completed"] == 1
    assert saved["measured_steps"] == 1
    assert saved["task_success_rate"] == 1.0


def test_metrics_count_retry_and_verification_failure(tmp_path):
    attempts = [0]
    metrics = ReliabilityMetrics()

    def verifier(step, output):
        attempts[0] += 1
        return (attempts[0] > 1, "ok" if attempts[0] > 1 else "not yet")

    report = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "memory.json"),
        executor=lambda step: "result",
        verifier=verifier,
        metrics=metrics,
    ).run("t1", "goal", Checklist.from_text("1. Esegui"))

    assert report.status == "completed"
    assert metrics.snapshot.retries == 1
    assert metrics.snapshot.verification_failures == 1


def test_recovery_policy_decisions():
    manager = RecoveryManager(request_human_after=3)

    assert manager.decide("execution_error", 1, 3).action == RecoveryAction.RETRY_STEP
    assert manager.decide("watchdog_timeout", 1, 3).action == RecoveryAction.RELOAD_CHECKPOINT
    assert manager.decide("execution_error", 3, 3).action == RecoveryAction.REQUEST_HUMAN


def test_checkpoint_is_updated_at_task_end(tmp_path):
    checkpoint = CheckpointManager(tmp_path / "checkpoint.json")
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "memory.json"),
        executor=lambda step: "ok",
        verifier=lambda step, output: (True, "verified"),
        checkpoint_manager=checkpoint,
    )

    orchestrator.run("t1", "goal", Checklist.from_text("1. Esegui"))

    saved = checkpoint.load()
    assert saved is not None
    assert saved.reason == "task_finished"
    assert saved.task["status"] == "completed"
