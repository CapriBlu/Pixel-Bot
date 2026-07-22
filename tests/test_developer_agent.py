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


def test_developer_ai_provider_parses_remote_changes(tmp_path):
    import json

    from pixel_bot.agent.ai_client import AIClientConfig
    from pixel_bot.developer import DeveloperAIProvider

    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-104", "Change", "Update app", allowed_paths=["src"])
    agent = DeveloperAgent(root, test_runner=PassingRunner())
    plan = agent.plan(task)
    snapshot = agent.analyzer.analyze()
    captured = {}

    def transport(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return {
            "changes": [
                {"path": "src/app.py", "content": "VALUE = 3\n", "reason": "upgrade"}
            ]
        }

    provider = DeveloperAIProvider(
        root,
        AIClientConfig(endpoint="https://example.invalid", max_requests_per_task=2),
        transport=transport,
    )
    changes = provider(task, snapshot, plan)

    assert changes[0].path == "src/app.py"
    assert captured["payload"]["response_format"] == "file_changes_v1"
    assert captured["payload"]["repository"]["relevant_file_contents"]
    assert provider.budget.requests_used == 1


def test_developer_ai_provider_dry_run_uses_programmed_changes(tmp_path):
    from pixel_bot.agent.ai_client import AIClientConfig
    from pixel_bot.developer import DeveloperAIProvider

    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-105", "Change", "Update app")
    agent = DeveloperAgent(root, test_runner=PassingRunner())
    provider = DeveloperAIProvider(
        root,
        AIClientConfig(dry_run=True),
        simulated_changes=[[FileChange("src/app.py", "VALUE = 4\n", "simulation")]],
    )

    changes = provider(task, agent.analyzer.analyze(), agent.plan(task))

    assert changes[0].content == "VALUE = 4\n"
    assert provider.budget.requests_used == 1


def test_developer_ai_provider_rejects_invalid_response(tmp_path):
    import pytest

    from pixel_bot.agent.ai_client import AIClientConfig
    from pixel_bot.developer import DeveloperAIProvider

    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-106", "Change", "Update app")
    agent = DeveloperAgent(root, test_runner=PassingRunner())
    provider = DeveloperAIProvider(
        root,
        AIClientConfig(endpoint="https://example.invalid"),
        transport=lambda request, timeout: {"changes": "invalid"},
    )

    with pytest.raises(RuntimeError, match="lista di modifiche"):
        provider(task, agent.analyzer.analyze(), agent.plan(task))


def init_git_repo(root: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "pixelbot@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Pixel Bot Tests"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True)


def test_git_manager_creates_task_branch_and_commit(tmp_path):
    import subprocess

    from pixel_bot.developer import GitManager

    root = make_repo(tmp_path)
    init_git_repo(root)
    (root / "src" / "app.py").write_text("VALUE = 5\n", encoding="utf-8")

    manager = GitManager(root)
    result = manager.publish(
        changed_files=["src/app.py"],
        task_id="PB-200",
        task_title="Update value",
    )

    assert result.branch == "pixelbot/pb-200-update-value"
    assert result.commit_sha
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True
    ).stdout.strip()
    assert branch == result.branch


def test_git_manager_rejects_unexpected_path(tmp_path):
    import pytest

    from pixel_bot.developer import GitManager

    root = make_repo(tmp_path)
    init_git_repo(root)
    manager = GitManager(root)

    with pytest.raises(ValueError, match="esce dal repository"):
        manager.commit_files(["../secret.txt"], "bad")


def test_developer_agent_can_commit_green_change(tmp_path):
    root = make_repo(tmp_path)
    init_git_repo(root)
    task = DevelopmentTask("PB-201", "Commit change", "Update app", allowed_paths=["src"])
    agent = DeveloperAgent(root, test_runner=PassingRunner())

    result = agent.run(
        task,
        change_provider=lambda task, snapshot, plan: [
            FileChange("src/app.py", "VALUE = 6\n", "upgrade")
        ],
        apply_changes=True,
        commit=True,
    )

    assert result.status == "committed"
    assert result.git and result.git["commit_sha"]
    assert result.git["branch"] == "pixelbot/pb-201-commit-change"


def test_task_loader_accepts_utf8_bom(tmp_path):
    root = make_repo(tmp_path)
    task_file = root / "tasks" / "PB-BOM.json"
    task_file.write_text(
        '{"task_id":"PB-BOM","title":"BOM","objective":"Read task"}',
        encoding="utf-8-sig",
    )

    task = TaskLoader(root / "tasks").load(task_file)

    assert task.task_id == "PB-BOM"


def test_developer_ai_provider_retries_timeout_then_succeeds(tmp_path):
    import json

    from pixel_bot.agent.ai_client import AIClientConfig
    from pixel_bot.developer import DeveloperAIProvider

    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-RETRY", "Retry", "Update app", allowed_paths=["src"])
    agent = DeveloperAgent(root, test_runner=PassingRunner())
    attempts = []
    delays = []

    def transport(request, timeout):
        attempts.append(timeout)
        if len(attempts) == 1:
            raise TimeoutError("temporary timeout")
        return {
            "changes": [
                {"path": "src/app.py", "content": "VALUE = 7\n", "reason": "retry"}
            ]
        }

    provider = DeveloperAIProvider(
        root,
        AIClientConfig(
            endpoint="https://example.invalid",
            max_requests_per_task=3,
            max_estimated_cost=1.0,
            max_retry_attempts=3,
            retry_backoff_seconds=0.25,
        ),
        transport=transport,
        sleeper=delays.append,
    )

    changes = provider(task, agent.analyzer.analyze(), agent.plan(task))

    assert changes[0].content == "VALUE = 7\n"
    assert provider.budget.requests_used == 2
    assert delays == [0.25]


def test_developer_agent_reports_exhausted_ai_retries(tmp_path):
    from pixel_bot.agent.ai_client import AIClientConfig
    from pixel_bot.developer import DeveloperAIProvider

    root = make_repo(tmp_path)
    task = DevelopmentTask("PB-FAIL", "Fail", "Update app", allowed_paths=["src"])
    report = root / "workspace" / "failed.json"
    provider = DeveloperAIProvider(
        root,
        AIClientConfig(
            endpoint="https://example.invalid",
            max_requests_per_task=2,
            max_estimated_cost=1.0,
            max_retry_attempts=2,
            retry_backoff_seconds=0,
        ),
        transport=lambda request, timeout: (_ for _ in ()).throw(TimeoutError("down")),
        sleeper=lambda delay: None,
    )

    result = DeveloperAgent(root, test_runner=PassingRunner()).run(
        task,
        change_provider=provider,
        apply_changes=True,
        report_path=report,
    )

    assert result.status == "failed"
    assert "dopo 2 tentativi" in (result.error or "")
    assert report.exists()
