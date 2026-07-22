from __future__ import annotations

import json
from pathlib import Path

from pixel_bot.developer.cli import main


def test_cli_next_task_marks_proposal_completed(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    task_path = tasks / "PB-008.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "PB-008",
                "title": "Queue demo",
                "objective": "Propose a documentation change",
                "allowed_paths": ["docs"],
                "test_command": ["python", "-c", "print('ok')"],
            }
        ),
        encoding="utf-8",
    )
    changes = tasks / "changes.json"
    changes.write_text(
        json.dumps([{"path": "docs/QUEUE.md", "content": "# Queue\n"}]),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--next-task",
            "--repo",
            str(tmp_path),
            "--changes",
            str(changes),
            "--report",
            "workspace/report.json",
        ]
    )

    assert exit_code == 0
    state = json.loads(
        (tmp_path / "workspace" / "developer-task-state.json").read_text(encoding="utf-8")
    )
    assert state["PB-008.json"]["status"] == "completed"
