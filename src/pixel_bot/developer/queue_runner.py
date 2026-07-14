from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pixel_bot.developer.models import DeveloperRunResult, DevelopmentPlan
from pixel_bot.developer.task_queue import QueuedTask, TaskQueue


@dataclass(slots=True)
class QueueRunItem:
    task_id: str
    task_path: str
    status: str
    report_path: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "task_id": self.task_id,
            "task_path": self.task_path,
            "status": self.status,
            "report_path": self.report_path,
            "error": self.error,
        }


@dataclass(slots=True)
class QueueRunSummary:
    status: str
    processed: int
    completed: int
    failed: int
    items: list[QueueRunItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "processed": self.processed,
            "completed": self.completed,
            "failed": self.failed,
            "items": [item.to_dict() for item in self.items],
        }


TaskExecutor = Callable[[QueuedTask, Path], DeveloperRunResult]


def run_task_queue(
    queue: TaskQueue,
    execute: TaskExecutor,
    reports_dir: Path,
    *,
    max_tasks: int = 5,
    stop_on_failure: bool = True,
) -> QueueRunSummary:
    """Run a bounded autonomous queue session.

    Each task is marked started before execution and persisted as completed or
    failed afterwards. The loop is deliberately bounded so an unattended run
    cannot consume an unlimited number of AI calls or repository mutations.
    """

    if max_tasks < 1:
        raise ValueError("max_tasks deve essere almeno 1.")

    reports_dir = reports_dir.resolve()
    items: list[QueueRunItem] = []
    completed = 0
    failed = 0

    while len(items) < max_tasks:
        queued = queue.next_task()
        if queued is None:
            status = "queue_empty" if not items else "completed"
            return QueueRunSummary(status, len(items), completed, failed, items)

        queue.mark_started(queued)
        report_path = reports_dir / f"{queued.task.task_id}-report.json"
        try:
            result = execute(queued, report_path)
        except Exception as exc:  # pragma: no cover - defensive boundary
            result = DeveloperRunResult(
                task_id=queued.task.task_id,
                status="failed",
                plan=DevelopmentPlan(queued.task, [], []),
                error=str(exc),
            )

        successful = result.status in {
            "ready_for_review",
            "changes_proposed",
            "committed",
            "pull_request_opened",
        }
        if successful:
            queue.mark_completed(queued, report_path)
            completed += 1
        else:
            queue.mark_failed(queued, result.error or result.status)
            failed += 1

        items.append(
            QueueRunItem(
                task_id=queued.task.task_id,
                task_path=str(queued.path),
                status=result.status,
                report_path=str(report_path),
                error=result.error,
            )
        )
        if not successful and stop_on_failure:
            return QueueRunSummary("stopped_on_failure", len(items), completed, failed, items)

    return QueueRunSummary("task_limit_reached", len(items), completed, failed, items)
