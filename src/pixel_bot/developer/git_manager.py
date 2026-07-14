from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

CommandRunner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def _default_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


@dataclass(slots=True)
class GitPublishResult:
    branch: str
    commit_sha: str | None = None
    pushed: bool = False
    pull_request_url: str | None = None


class GitManager:
    """Safe Git operations for Developer Agent.

    The manager never commits directly to protected branches and stages only the
    file paths explicitly supplied by the caller. Network actions are opt-in.
    """

    protected_branches = frozenset({"main", "master", "production", "release"})

    def __init__(self, repository_root: Path, runner: CommandRunner | None = None) -> None:
        self.repository_root = repository_root.resolve()
        self.runner = runner or _default_runner

    def ensure_repository(self) -> None:
        result = self._run("git", "rev-parse", "--is-inside-work-tree")
        if result.returncode != 0 or result.stdout.strip() != "true":
            raise RuntimeError("La cartella non è un repository Git valido.")

    def current_branch(self) -> str:
        self.ensure_repository()
        result = self._checked("git", "branch", "--show-current")
        branch = result.stdout.strip()
        if not branch:
            raise RuntimeError("HEAD scollegata: impossibile determinare la branch corrente.")
        return branch

    def is_clean(self) -> bool:
        self.ensure_repository()
        result = self._checked("git", "status", "--porcelain")
        return not result.stdout.strip()

    def create_task_branch(self, task_id: str, title: str, *, base: str | None = None) -> str:
        self.ensure_repository()
        slug = self._slugify(f"{task_id}-{title}")
        branch = f"pixelbot/{slug}"
        command = ["git", "switch", "-c", branch]
        if base:
            command.append(base)
        result = self._run(*command)
        if result.returncode != 0:
            # Reuse an existing local branch only when it can be switched safely.
            result = self._run("git", "switch", branch)
        if result.returncode != 0:
            raise RuntimeError(self._error_message("Creazione branch fallita", result))
        return branch

    def commit_files(self, paths: Sequence[str], message: str) -> str:
        normalized = self._validate_paths(paths)
        branch = self.current_branch()
        if branch in self.protected_branches:
            raise RuntimeError(f"Commit automatico vietato sulla branch protetta: {branch}")
        if not normalized:
            raise RuntimeError("Nessun file autorizzato da aggiungere al commit.")
        self._checked("git", "add", "--", *normalized)
        staged = self._checked("git", "diff", "--cached", "--name-only").stdout.splitlines()
        staged_set = {item.strip().replace("\\", "/") for item in staged if item.strip()}
        if not staged_set:
            raise RuntimeError("Nessuna modifica Git da committare.")
        unexpected = staged_set.difference(normalized)
        if unexpected:
            self._run("git", "reset")
            raise RuntimeError(f"Git ha preparato file inattesi: {sorted(unexpected)}")
        result = self._run("git", "commit", "-m", message)
        if result.returncode != 0:
            raise RuntimeError(self._error_message("Commit fallito", result))
        return self._checked("git", "rev-parse", "HEAD").stdout.strip()

    def push(self, branch: str, *, remote: str = "origin") -> None:
        if branch in self.protected_branches:
            raise RuntimeError(f"Push automatico vietato sulla branch protetta: {branch}")
        result = self._run("git", "push", "-u", remote, branch)
        if result.returncode != 0:
            raise RuntimeError(self._error_message("Push fallito", result))

    def open_draft_pr(
        self,
        *,
        title: str,
        body: str,
        base: str = "main",
    ) -> str:
        branch = self.current_branch()
        if branch in self.protected_branches:
            raise RuntimeError("Impossibile aprire una PR dalla branch protetta.")
        result = self._run(
            "gh",
            "pr",
            "create",
            "--draft",
            "--base",
            base,
            "--head",
            branch,
            "--title",
            title,
            "--body",
            body,
        )
        if result.returncode != 0:
            raise RuntimeError(self._error_message("Creazione Pull Request fallita", result))
        url = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
        if not url.startswith("http"):
            raise RuntimeError("GitHub CLI non ha restituito l'URL della Pull Request.")
        return url

    def publish(
        self,
        *,
        changed_files: Sequence[str],
        task_id: str,
        task_title: str,
        commit_message: str | None = None,
        push: bool = False,
        open_pr: bool = False,
        pr_body: str = "",
        base: str = "main",
    ) -> GitPublishResult:
        branch = self.current_branch()
        if branch in self.protected_branches:
            branch = self.create_task_branch(task_id, task_title, base=branch)
        sha = self.commit_files(
            changed_files,
            commit_message or f"{task_id}: {task_title}",
        )
        result = GitPublishResult(branch=branch, commit_sha=sha)
        if push or open_pr:
            self.push(branch)
            result.pushed = True
        if open_pr:
            result.pull_request_url = self.open_draft_pr(
                title=f"{task_id}: {task_title}",
                body=pr_body,
                base=base,
            )
        return result

    def _validate_paths(self, paths: Sequence[str]) -> list[str]:
        normalized: list[str] = []
        for value in paths:
            if not value or Path(value).is_absolute():
                raise ValueError(f"Percorso Git non valido: {value!r}")
            target = (self.repository_root / value).resolve()
            try:
                relative = target.relative_to(self.repository_root).as_posix()
            except ValueError as error:
                raise ValueError(f"Il percorso esce dal repository: {value}") from error
            normalized.append(relative)
        return sorted(set(normalized))

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return slug[:60] or "task"

    def _run(self, *command: str) -> subprocess.CompletedProcess[str]:
        return self.runner(command, self.repository_root)

    def _checked(self, *command: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*command)
        if result.returncode != 0:
            raise RuntimeError(self._error_message("Comando Git fallito", result))
        return result

    @staticmethod
    def _error_message(prefix: str, result: subprocess.CompletedProcess[str]) -> str:
        detail = (result.stderr or result.stdout).strip()
        return f"{prefix}: {detail or 'errore sconosciuto'}"
