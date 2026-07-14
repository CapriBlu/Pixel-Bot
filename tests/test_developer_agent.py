from pathlib import Path

from pixel_bot.developer import (
    DeveloperAgent,
    DevelopmentTask,
    FileChange,
    RepositoryAnalyzer,
    TaskLoader,
    TestResult as DeveloperTestResult,
)


class PassingRunner:
    def run(self, command):
        return DeveloperTestResult(command=list(command), return_code=0, stdout="ok", stderr="")


class FailingRunner:
    def run(self, command):
        return DeveloperTestResult(command=list(command), return_code=1, stdout="", stderr="fail")


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tasks").mkdir()
    (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "tests" / "test_app.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    return root


def test_repository_analyzer_builds_snapshot(tmp_path):
    root = make_repo(tmp_path)
    snapshot = RepositoryAnalyzer(root).analyze()

    assert "src/app.py" in snapshot.python_files
    assert "tests/test_app.py" in snapshot.test_files


def test_task_loader_reads_json(tmp_path):
    root = make_repo(tmp_path)
    task_file = root / "tasks" / "PB-100.json"
    task_file.write_text(
        '{"task_id":"PB-100","title":"Test","objective":"Update app"}',
        encoding="utf-8",
    )

    task = TaskLoader(root / "tasks").load_next()

    assert task is not None
    assert task.task_id == "PB-100"


def test_developer_agent_applies_change_and_passes_tests(tmp_path):
    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-101", "Change", "Update app", allowed_paths=["src"])
    agent = DeveloperAgent(root, test_runner=PassingRunner())

    result = agent.run(
        task,
        change_provider=lambda task, snapshot, plan: [
            FileChange("src/app.py", "VALUE = 2\n", "update")
        ],
        apply_changes=True,
        report_path=root / "report.json",
    )

    assert result.status == "ready_for_review"
    assert (root / "src" / "app.py").read_text(encoding="utf-8") == "VALUE = 2\n"
    assert (root / "report.json").exists()


def test_developer_agent_rolls_back_failed_change(tmp_path):
    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-102", "Change", "Update app", allowed_paths=["src"])
    agent = DeveloperAgent(root, test_runner=FailingRunner())

    result = agent.run(
        task,
        change_provider=lambda task, snapshot, plan: [
            FileChange("src/app.py", "BROKEN = True\n", "bad")
        ],
        apply_changes=True,
    )

    assert result.status == "tests_failed_rolled_back"
    assert (root / "src" / "app.py").read_text(encoding="utf-8") == "VALUE = 1\n"


def test_developer_agent_rejects_path_outside_allowlist(tmp_path):
    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-103", "Change", "Update", allowed_paths=["src"])
    agent = DeveloperAgent(root, test_runner=PassingRunner())

    result = agent.run(
        task,
        change_provider=lambda task, snapshot, plan: [
            FileChange("README.md", "not allowed", "bad")
        ],
        apply_changes=True,
    )

    assert result.status == "failed"
    assert "non autorizzato" in (result.error or "")
