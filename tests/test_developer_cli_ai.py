import json
from pathlib import Path

import pytest

from pixel_bot.developer.cli import _build_change_provider, build_parser
from pixel_bot.developer.models import DevelopmentPlan, DevelopmentTask, RepositorySnapshot


def test_cli_rejects_publish_without_apply():
    parser = build_parser()
    args = parser.parse_args(["task.json", "--open-pr"])
    assert args.open_pr is True
    assert args.apply is False


def test_cli_builds_dry_run_ai_provider(tmp_path, monkeypatch):
    changes_path = tmp_path / "changes.json"
    changes_path.write_text(
        json.dumps([{"path": "docs/result.md", "content": "ok\n", "reason": "test"}]),
        encoding="utf-8",
    )
    monkeypatch.setenv("PIXEL_BOT_DRY_RUN", "1")
    args = build_parser().parse_args(
        ["task.json", "--ai", "--simulation-changes", str(changes_path)]
    )
    provider = _build_change_provider(args, tmp_path)
    task = DevelopmentTask("PB-X", "Test", "Create docs", allowed_paths=["docs"])
    snapshot = RepositorySnapshot(tmp_path, [], [], [], [])
    plan = DevelopmentPlan(task, [], [])

    changes = provider(task, snapshot, plan)

    assert changes[0].path == "docs/result.md"
    assert provider.budget.requests_used == 1
    assert (tmp_path / "workspace").exists()


def test_cli_simulation_changes_require_dry_run(tmp_path, monkeypatch):
    changes_path = tmp_path / "changes.json"
    changes_path.write_text("[]", encoding="utf-8")
    monkeypatch.delenv("PIXEL_BOT_DRY_RUN", raising=False)
    monkeypatch.setenv("PIXEL_BOT_AI_ENDPOINT", "https://example.invalid")
    args = build_parser().parse_args(
        ["task.json", "--ai", "--simulation-changes", str(changes_path)]
    )

    with pytest.raises(ValueError, match="PIXEL_BOT_DRY_RUN"):
        _build_change_provider(args, tmp_path)
