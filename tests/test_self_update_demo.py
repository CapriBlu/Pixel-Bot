from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pixel_bot.developer.cli import main


def _init_repository(root: Path) -> None:
    (root / "docs").mkdir(parents=True)
    (root / "tasks").mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "pixelbot@example.invalid"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Pixel Bot Tests"], cwd=root, check=True)
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True
    )


def test_controlled_self_update_demo_creates_branch_commit_and_report(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    _init_repository(root)

    task_path = root / "tasks" / "PB-007.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "PB-007",
                "title": "Self update demo",
                "objective": "Create a controlled documentation update",
                "acceptance_criteria": ["Documentation exists"],
                "allowed_paths": ["docs"],
                "test_command": [sys.executable, "-c", "print('tests passed')"],
            }
        ),
        encoding="utf-8",
    )
    changes_path = root / "tasks" / "PB-007.changes.json"
    changes_path.write_text(
        json.dumps(
            [
                {
                    "path": "docs/SELF_UPDATE_DEMO.md",
                    "content": "# Autonomous update completed\n",
                    "reason": "end-to-end proof",
                }
            ]
        ),
        encoding="utf-8",
    )
    report_path = root / "workspace" / "PB-007-report.json"
    monkeypatch.setenv("PIXEL_BOT_DRY_RUN", "1")

    exit_code = main(
        [
            str(task_path),
            "--repo",
            str(root),
            "--ai",
            "--simulation-changes",
            str(changes_path),
            "--apply",
            "--commit",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    assert (root / "docs" / "SELF_UPDATE_DEMO.md").read_text(encoding="utf-8") == (
        "# Autonomous update completed\n"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "committed"
    assert report["test_result"]["passed"] is True
    assert report["git"]["commit_sha"]
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert branch == "pixelbot/pb-007-self-update-demo"
