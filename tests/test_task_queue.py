from __future__ import annotations

import json
from pathlib import Path

from pixel_bot.developer.task_queue import TaskQueue


def _write_task(tasks: Path, name: str, task_id: str, priority: int) -> None:
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


def test_task_queue_orders_by_priority_and_persists_completion(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    state = tmp_path / "workspace" / "queue.json"
    _write_task(tasks, "later.json", "PB-200", 20)
    _write_task(tasks, "first.json", "PB-100", 10)

    queue = TaskQueue(tasks, state)
    queued = queue.next_task()
    assert queued is not None
    assert queued.task.task_id == "PB-100"

    queue.mark_started(queued)
    queue.mark_completed(queued, tmp_path / "report.json")

    next_queued = TaskQueue(tasks, state).next_task()
    assert next_queued is not None
    assert next_queued.task.task_id == "PB-200"
    snapshot = queue.snapshot()
    assert snapshot["first.json"]["status"] == "completed"
    assert snapshot["first.json"]["attempts"] == 1


def test_task_queue_stops_retrying_after_max_attempts(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    state = tmp_path / "workspace" / "queue.json"
    _write_task(tasks, "task.json", "PB-300", 10)
    queue = TaskQueue(tasks, state, max_attempts=2)

    for _ in range(2):
        queued = queue.next_task()
        assert queued is not None
        queue.mark_started(queued)
        queue.mark_failed(queued, "boom")

    assert queue.next_task() is None
    assert queue.snapshot()["task.json"]["status"] == "failed"
