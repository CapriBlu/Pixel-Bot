import json

import pytest

from pixel_bot.developer.autonomous_orchestrator import AutonomousOrchestrator, RetryPolicy
from pixel_bot.developer.autonomous_planner import AutonomousPlanner
from pixel_bot.developer.checklist_engine import Checklist
from pixel_bot.developer.task_memory import PersistentTaskMemory, TaskRecord


def build_orchestrator(tmp_path, executor, verifier, attempts=3):
    return AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "task.json"),
        executor=executor,
        verifier=verifier,
        retry_policy=RetryPolicy(max_attempts=attempts),
        report_path=tmp_path / "report.json",
    )


def test_completes_and_writes_report(tmp_path):
    checklist = Checklist.from_text("1. Analizza\n2. Verifica")
    orchestrator = build_orchestrator(
        tmp_path,
        executor=lambda step: {"step": step.id},
        verifier=lambda step, output: (output["step"] == step.id, "ok"),
    )

    report = orchestrator.run("task-1", "goal", checklist)

    assert report.status == "completed"
    assert report.completed_steps == 2
    assert report.total_steps == 2
    assert checklist.is_complete
    saved = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert saved["status"] == "completed"


def test_retries_then_succeeds(tmp_path):
    attempts = {"count": 0}

    def executor(step):
        attempts["count"] += 1
        return attempts["count"]

    orchestrator = build_orchestrator(
        tmp_path,
        executor=executor,
        verifier=lambda step, output: (output >= 2, f"tentativo {output}"),
    )

    report = orchestrator.run("task-1", "goal", Checklist.from_text("1. Esegui"))

    assert report.status == "completed"
    assert report.steps[0].attempts == 2


def test_fails_after_retry_limit(tmp_path):
    orchestrator = build_orchestrator(
        tmp_path,
        executor=lambda step: None,
        verifier=lambda step, output: (False, "manca evidenza"),
        attempts=2,
    )

    report = orchestrator.run("task-1", "goal", Checklist.from_text("1. Esegui"))

    assert report.status == "failed"
    assert report.steps[0].attempts == 2
    assert "evidenza" in report.steps[0].error


def test_resumes_completed_step(tmp_path):
    memory = PersistentTaskMemory(tmp_path / "task.json")
    record = TaskRecord(task_id="task-1", goal="goal")
    record.context["steps"] = [
        {"id": 1, "objective": "Analizza", "depends_on": [], "status": "completed", "attempts": 1, "evidence": "gia fatto"},
        {"id": 2, "objective": "Verifica", "depends_on": [1], "status": "pending", "attempts": 0, "evidence": ""},
    ]
    memory.save(record)
    executed = []
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=memory,
        executor=lambda step: executed.append(step.id) or step.id,
        verifier=lambda step, output: (True, "ok"),
    )

    report = orchestrator.run("task-1", "goal", Checklist.from_text("1. Analizza\n2. Verifica"))

    assert report.resumed is True
    assert executed == [2]
    assert report.status == "completed"


def test_rejects_different_task_in_same_memory(tmp_path):
    memory = PersistentTaskMemory(tmp_path / "task.json")
    memory.save(TaskRecord(task_id="old", goal="old goal"))
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=memory,
        executor=lambda step: None,
        verifier=lambda step, output: (True, "ok"),
    )

    with pytest.raises(ValueError, match="old"):
        orchestrator.run("new", "new goal", Checklist.from_text("1. Esegui"))


def test_retry_policy_validation():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        RetryPolicy(delay_seconds=-1)


def test_executor_error_is_classified(tmp_path):
    def executor(step):
        raise RuntimeError("boom")

    report = build_orchestrator(tmp_path, executor, lambda step, output: (True, "ok"), attempts=1).run(
        "task-1", "goal", Checklist.from_text("1. Esegui")
    )

    assert report.status == "failed"
    assert report.steps[0].error_type == "execution_error"


def test_verifier_error_is_classified(tmp_path):
    def verifier(step, output):
        raise RuntimeError("verifier rotto")

    report = build_orchestrator(tmp_path, lambda step: object(), verifier, attempts=1).run(
        "task-1", "goal", Checklist.from_text("1. Esegui")
    )

    assert report.status == "failed"
    assert report.steps[0].error_type == "verification_error"


def test_max_rounds_bounds_execution(tmp_path):
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "task.json"),
        executor=lambda step: None,
        verifier=lambda step, output: (False, "no"),
        retry_policy=RetryPolicy(max_attempts=3),
        max_rounds=1,
    )

    report = orchestrator.run("task-1", "goal", Checklist.from_text("1. Esegui"))

    assert report.status == "bounded"
    assert report.rounds == 1


def test_resume_continues_retry_counter(tmp_path):
    memory = PersistentTaskMemory(tmp_path / "task.json")
    record = TaskRecord(task_id="task-1", goal="goal", status="retrying")
    record.context["rounds"] = 1
    record.context["steps"] = [
        {
            "id": 1,
            "objective": "Esegui",
            "depends_on": [],
            "status": "retrying",
            "attempts": 1,
            "evidence": "",
            "error": "temporaneo",
        }
    ]
    memory.save(record)
    calls = []
    orchestrator = AutonomousOrchestrator(
        planner=AutonomousPlanner(),
        memory=memory,
        executor=lambda step: calls.append(step.id) or "ok",
        verifier=lambda step, output: (True, "fatto"),
        retry_policy=RetryPolicy(max_attempts=3),
    )

    report = orchestrator.run("task-1", "goal", Checklist.from_text("1. Esegui"))

    assert report.status == "completed"
    assert report.steps[0].attempts == 2
    assert report.rounds == 2
    assert calls == [1]
