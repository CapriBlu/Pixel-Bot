from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

from pixel_bot.update_readiness import CheckResult, determine_status, run_update_readiness_check


def test_determine_status_prioritizes_red() -> None:
    checks = [
        CheckResult("a", "A", "green", "ok"),
        CheckResult("b", "B", "orange", "warning"),
        CheckResult("c", "C", "red", "failure", blocking=True),
    ]
    assert determine_status(checks) == "red"


def test_determine_status_orange_for_operator_action() -> None:
    checks = [CheckResult("a", "A", "green", "decision", operator_action=True)]
    assert determine_status(checks) == "orange"


def test_invalid_repository_is_red(tmp_path: Path) -> None:
    def runner(command: list[str], cwd: Path, timeout: int) -> CompletedProcess[str]:
        return CompletedProcess(command, 128, "", "not a repository")

    report = run_update_readiness_check(tmp_path, runner=runner, run_tests=False, save_report=False)
    assert report.status == "red"
    assert report.ready_for_update is False
    assert any(item.code == "repo_invalid" for item in report.checks)
