from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pixel_bot.developer.git_manager import GitManager
from pixel_bot.developer.models import (
    DeveloperRunResult,
    DevelopmentPlan,
    DevelopmentTask,
    FileChange,
    RepositorySnapshot,
)
from pixel_bot.developer.repository import RepositoryAnalyzer
from pixel_bot.developer.testing import TestRunner

ChangeProvider = Callable[[DevelopmentTask, RepositorySnapshot, DevelopmentPlan], list[FileChange]]


@dataclass(slots=True)
class DeveloperAgent:
    repository_root: Path
    analyzer: RepositoryAnalyzer | None = None
    test_runner: TestRunner | None = None
    git_manager: GitManager | None = None

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        self.analyzer = self.analyzer or RepositoryAnalyzer(self.repository_root)
        self.test_runner = self.test_runner or TestRunner(self.repository_root)
        self.git_manager = self.git_manager or GitManager(self.repository_root)

    def plan(self, task: DevelopmentTask) -> DevelopmentPlan:
        snapshot = self.analyzer.analyze()
        relevant = self.analyzer.relevant_files(task.objective, snapshot)
        return DevelopmentPlan(
            task=task,
            relevant_files=relevant,
            steps=[
                "Analizzare i file rilevanti e i criteri di accettazione.",
                "Generare modifiche esclusivamente nei percorsi autorizzati.",
                "Applicare le modifiche con backup locale.",
                "Eseguire i test configurati dal task.",
                "Produrre un report tracciabile per revisione e commit.",
            ],
            risks=[
                "Una modifica generata automaticamente può richiedere revisione umana.",
                "I test non garantiscono da soli la correttezza funzionale completa.",
            ],
        )

    def run(
        self,
        task: DevelopmentTask,
        *,
        change_provider: ChangeProvider | None = None,
        apply_changes: bool = False,
        report_path: Path | None = None,
        commit: bool = False,
        push: bool = False,
        open_pr: bool = False,
        pr_base: str = "main",
    ) -> DeveloperRunResult:
        plan = self.plan(task)
        snapshot = self.analyzer.analyze()
        changes = change_provider(task, snapshot, plan) if change_provider else []
        plan.proposed_changes = list(changes)

        if changes and not apply_changes:
            result = DeveloperRunResult(task.task_id, "changes_proposed", plan)
            self._write_report(result, report_path)
            return result

        backups: list[tuple[Path, Path | None]] = []
        changed_files: list[str] = []
        try:
            if apply_changes:
                for change in changes:
                    target = self._validated_target(change.path, task.allowed_paths)
                    backup = self._backup(target)
                    backups.append((target, backup))
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(change.content, encoding="utf-8")
                    changed_files.append(target.relative_to(self.repository_root).as_posix())

            test_result = self.test_runner.run(task.test_command)
            status = "ready_for_review" if test_result.passed else "tests_failed"
            result = DeveloperRunResult(
                task_id=task.task_id,
                status=status,
                plan=plan,
                changed_files=changed_files,
                test_result=test_result,
            )
            if test_result.passed and commit and changed_files:
                publication = self.git_manager.publish(
                    changed_files=changed_files,
                    task_id=task.task_id,
                    task_title=task.title,
                    push=push,
                    open_pr=open_pr,
                    base=pr_base,
                    pr_body=self._pull_request_body(task, plan, test_result),
                )
                result.git = {
                    "branch": publication.branch,
                    "commit_sha": publication.commit_sha,
                    "pushed": publication.pushed,
                    "pull_request_url": publication.pull_request_url,
                }
                result.status = "pull_request_opened" if publication.pull_request_url else "committed"
            if not test_result.passed and backups:
                self._restore(backups)
                result.changed_files = []
                result.status = "tests_failed_rolled_back"
            self._write_report(result, report_path)
            return result
        except Exception as error:
            if backups:
                self._restore(backups)
            result = DeveloperRunResult(
                task_id=task.task_id,
                status="failed",
                plan=plan,
                changed_files=[],
                error=str(error),
            )
            self._write_report(result, report_path)
            return result

    @staticmethod
    def _pull_request_body(task: DevelopmentTask, plan: DevelopmentPlan, test_result) -> str:
        criteria = "\n".join(f"- {item}" for item in task.acceptance_criteria) or "- Non specificati"
        files = "\n".join(f"- `{item.path}`: {item.reason}" for item in plan.proposed_changes) or "- Nessuno"
        return (
            f"## Obiettivo\n{task.objective}\n\n"
            f"## Criteri di accettazione\n{criteria}\n\n"
            f"## File modificati\n{files}\n\n"
            f"## Test\n`{' '.join(test_result.command)}`: {'PASS' if test_result.passed else 'FAIL'}\n"
            "\nCreato da Pixel Bot Developer Agent. Merge subordinato a revisione umana."
        )

    def _validated_target(self, relative_path: str, allowed_paths: list[str]) -> Path:
        if not relative_path or Path(relative_path).is_absolute():
            raise ValueError("Percorso modifica non valido.")
        target = (self.repository_root / relative_path).resolve()
        try:
            relative = target.relative_to(self.repository_root)
        except ValueError as error:
            raise ValueError("La modifica esce dal repository.") from error
        top_level = relative.parts[0] if relative.parts else ""
        normalized_allowed = {Path(item).parts[0] for item in allowed_paths if Path(item).parts}
        if top_level not in normalized_allowed:
            raise ValueError(f"Percorso non autorizzato per il task: {relative_path}")
        return target

    @staticmethod
    def _backup(target: Path) -> Path | None:
        if not target.exists():
            return None
        backup = target.with_suffix(target.suffix + ".pixelbot.bak")
        shutil.copy2(target, backup)
        return backup

    @staticmethod
    def _restore(backups: list[tuple[Path, Path | None]]) -> None:
        for target, backup in reversed(backups):
            if backup is None:
                target.unlink(missing_ok=True)
            else:
                shutil.move(str(backup), str(target))

    @staticmethod
    def _write_report(result: DeveloperRunResult, report_path: Path | None) -> None:
        if report_path is None:
            return
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
