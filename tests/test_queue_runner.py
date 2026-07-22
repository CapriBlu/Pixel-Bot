from __future__ import annotations

import json
from pathlib import Path

from pixel_bot.developer.models import DeveloperRunResult, DevelopmentPlan
from pixel_bot.developer.queue_runner import run_task_queue
from pixel_bot.developer.task_queue import TaskQueue


def _task(tasks: Path, name: str, task_id: str, priority: int) -> None:
    (tasks / name).write_text(
        json.dumps(
            {
                "task_id": task_id,
                "title": task_id,
                "objective": "demo",
                "metadata": {"priority": priority},
            }
        ),
        encoding="utf-8",
    )


def test_queue_runner_processes_tasks_until_limit(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    _task(tasks, "one.json", "PB-1", 1)
    _task(tasks, "two.json", "PB-2", 2)
    queue = TaskQueue(tasks, tmp_path / "workspace" / "state.json")

    def execute(queued, report_path):
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("{}", encoding="utf-8")
        return DeveloperRunResult(task_id=queued.task.task_id, status="committed", plan=DevelopmentPlan(queued.task, [], []))

    summary = run_task_queue(queue, execute, tmp_path / "reports", max_tasks=1)

    assert summary.status == "task_limit_reached"
    assert summary.processed == 1
    assert summary.completed == 1
    assert queue.next_task().task.task_id == "PB-2"


def test_queue_runner_stops_on_failure_by_default(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    _task(tasks, "one.json", "PB-1", 1)
    _task(tasks, "two.json", "PB-2", 2)
    queue = TaskQueue(tasks, tmp_path / "workspace" / "state.json")

    def execute(queued, report_path):
        return DeveloperRunResult(task_id=queued.task.task_id, status="failed", plan=DevelopmentPlan(queued.task, [], []), error="boom")

    summary = run_task_queue(queue, execute, tmp_path / "reports", max_tasks=2)

    assert summary.status == "stopped_on_failure"
    assert summary.processed == 1
    assert summary.failed == 1
    assert summary.items[0].error == "boom"


def test_queue_runner_reports_empty_queue(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    queue = TaskQueue(tasks, tmp_path / "workspace" / "state.json")

    summary = run_task_queue(queue, lambda *_: None, tmp_path / "reports")

    assert summary.status == "queue_empty"
    assert summary.processed == 0


def test_queue_runner_honors_control_check_before_next_task(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    _task(tasks, "one.json", "PB-1", 1)
    queue = TaskQueue(tasks, tmp_path / "workspace" / "state.json")

    summary = run_task_queue(
        queue,
        lambda *_: None,
        tmp_path / "reports",
        control_check=lambda: "paused",
    )

    assert summary.status == "paused"
    assert summary.processed == 0
    assert queue.next_task() is not None
