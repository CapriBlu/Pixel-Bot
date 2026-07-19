from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


@dataclass(slots=True)
class CheckResult:
    code: str
    title: str
    status: str
    message: str
    operator_action: bool = False
    blocking: bool = False
    details: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ReadinessReport:
    status: str
    ready_for_update: bool
    timestamp: str
    repository: str
    checks: list[CheckResult]
    report_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["checks"] = [asdict(item) for item in self.checks]
        return payload


Runner = Callable[[list[str], Path, int], subprocess.CompletedProcess[str]]


def _run(command: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _git(repo: Path, *args: str, runner: Runner = _run, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return runner(["git", *args], repo, timeout)


def _result(
    code: str,
    title: str,
    status: str,
    message: str,
    *,
    operator_action: bool = False,
    blocking: bool = False,
    **details: object,
) -> CheckResult:
    return CheckResult(
        code=code,
        title=title,
        status=status,
        message=message,
        operator_action=operator_action,
        blocking=blocking,
        details=details,
    )


def _check_repository(repo: Path, runner: Runner) -> list[CheckResult]:
    if not repo.exists():
        return [_result("repo_missing", "Repository", "red", "La cartella del repository non esiste.", blocking=True)]
    probe = _git(repo, "rev-parse", "--is-inside-work-tree", runner=runner)
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return [_result("repo_invalid", "Repository", "red", "La cartella non e un repository Git valido.", blocking=True)]
    branch = _git(repo, "branch", "--show-current", runner=runner).stdout.strip()
    if not branch:
        return [_result("detached_head", "Branch Git", "orange", "HEAD scollegato: selezionare una branch prima dell'aggiornamento.", operator_action=True)]
    return [_result("repo_ok", "Repository", "green", f"Repository valido. Branch corrente: {branch}.", branch=branch)]


def _check_git_state(repo: Path, runner: Runner) -> list[CheckResult]:
    results: list[CheckResult] = []
    status = _git(repo, "status", "--porcelain=v1", runner=runner)
    if status.returncode != 0:
        return [_result("git_status_failed", "Stato Git", "red", "Impossibile leggere lo stato Git.", blocking=True, stderr=status.stderr.strip())]

    lines = [line for line in status.stdout.splitlines() if line.strip()]
    tracked_changes = [line for line in lines if not line.startswith("??")]
    untracked = [line[3:] for line in lines if line.startswith("??")]

    if tracked_changes:
        results.append(_result(
            "working_tree_changes",
            "Modifiche locali",
            "orange",
            f"Sono presenti {len(tracked_changes)} modifiche tracciate da esaminare prima dell'aggiornamento.",
            operator_action=True,
            files=tracked_changes[:50],
        ))
    else:
        results.append(_result("working_tree_clean", "Modifiche locali", "green", "Nessuna modifica tracciata pendente."))

    if untracked:
        results.append(_result(
            "untracked_files",
            "File non tracciati",
            "orange",
            f"Sono presenti {len(untracked)} file o cartelle non tracciati da classificare.",
            operator_action=True,
            files=untracked[:50],
        ))
    else:
        results.append(_result("untracked_clear", "File non tracciati", "green", "Nessun file non tracciato."))

    conflicts = _git(repo, "diff", "--name-only", "--diff-filter=U", runner=runner)
    conflict_files = [line for line in conflicts.stdout.splitlines() if line.strip()]
    if conflicts.returncode != 0:
        results.append(_result("conflict_check_failed", "Conflitti Git", "red", "Impossibile verificare i conflitti Git.", blocking=True))
    elif conflict_files:
        results.append(_result("git_conflicts", "Conflitti Git", "red", f"Rilevati {len(conflict_files)} conflitti Git.", blocking=True, files=conflict_files))
    else:
        results.append(_result("git_conflicts_clear", "Conflitti Git", "green", "Nessun conflitto Git rilevato."))

    upstream = _git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", runner=runner)
    if upstream.returncode != 0:
        results.append(_result("no_upstream", "Sincronizzazione remota", "orange", "La branch non ha un upstream configurato.", operator_action=True))
    else:
        counts = _git(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}", runner=runner)
        try:
            ahead, behind = [int(value) for value in counts.stdout.split()[:2]]
        except (ValueError, IndexError):
            results.append(_result("divergence_unknown", "Sincronizzazione remota", "orange", "Non e stato possibile determinare la divergenza dal remoto.", operator_action=True))
        else:
            if behind > 0:
                results.append(_result("branch_behind", "Sincronizzazione remota", "orange", f"La branch e indietro di {behind} commit rispetto al remoto.", operator_action=True, ahead=ahead, behind=behind))
            elif ahead > 0:
                results.append(_result("branch_ahead", "Sincronizzazione remota", "orange", f"La branch contiene {ahead} commit locali non pubblicati.", operator_action=True, ahead=ahead, behind=behind))
            else:
                results.append(_result("branch_synced", "Sincronizzazione remota", "green", "La branch e allineata al remoto.", ahead=0, behind=0))
    return results


def _check_dependencies(repo: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    pyproject = repo / "pyproject.toml"
    requirements = repo / "requirements.txt"
    if not pyproject.exists():
        results.append(_result("pyproject_missing", "Configurazione Python", "red", "pyproject.toml non trovato.", blocking=True))
    else:
        results.append(_result("pyproject_ok", "Configurazione Python", "green", "pyproject.toml presente."))

    if requirements.exists():
        raw = requirements.read_bytes()
        if b"\x00" in raw or raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            results.append(_result("requirements_encoding", "requirements.txt", "orange", "requirements.txt non e codificato in UTF-8 standard.", operator_action=True))
        else:
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                results.append(_result("requirements_decode", "requirements.txt", "orange", "requirements.txt non e leggibile come UTF-8.", operator_action=True))
            else:
                results.append(_result("requirements_ok", "requirements.txt", "green", "requirements.txt leggibile in UTF-8."))
    else:
        results.append(_result("requirements_missing", "requirements.txt", "orange", "requirements.txt non presente; verificare che pyproject.toml sia la fonte unica dichiarata.", operator_action=True))
    return results


def _check_environment(repo: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    workspace = repo / "workspace"
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        probe = workspace / ".pixelbot-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as error:
        results.append(_result("workspace_unwritable", "Workspace", "red", "La cartella workspace non e scrivibile.", blocking=True, error=str(error)))
    else:
        results.append(_result("workspace_ok", "Workspace", "green", "La cartella workspace e scrivibile."))

    free_bytes = shutil.disk_usage(repo).free
    free_mb = free_bytes // (1024 * 1024)
    if free_mb < 500:
        results.append(_result("disk_low", "Spazio disponibile", "red", f"Spazio libero insufficiente: {free_mb} MB.", blocking=True, free_mb=free_mb))
    elif free_mb < 2048:
        results.append(_result("disk_warning", "Spazio disponibile", "orange", f"Spazio libero limitato: {free_mb} MB.", operator_action=True, free_mb=free_mb))
    else:
        results.append(_result("disk_ok", "Spazio disponibile", "green", f"Spazio libero disponibile: {free_mb} MB.", free_mb=free_mb))

    env_file = repo / ".env"
    if env_file.exists():
        results.append(_result("env_present", "Configurazione .env", "green", ".env presente; i valori non sono stati letti ne mostrati."))
    else:
        results.append(_result("env_missing", "Configurazione .env", "orange", ".env non presente. Verificare se e necessario per il prossimo aggiornamento.", operator_action=True))
    return results


def _project_python(repo: Path) -> str:
    candidates = [
        repo / ".venv" / "Scripts" / "python.exe",
        repo / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def _check_tests(repo: Path, runner: Runner) -> list[CheckResult]:
    executable = _project_python(repo)
    completed = runner([executable, "-m", "pytest", "-q"], repo, 300)
    output = (completed.stdout + "\n" + completed.stderr).strip()
    tail = "\n".join(output.splitlines()[-12:])
    if completed.returncode == 0:
        return [_result("tests_passed", "Test automatici", "green", "Suite pytest completata con successo.", output=tail)]
    if "No module named pytest" in output:
        return [_result("pytest_missing", "Test automatici", "orange", "pytest non e installato nell'ambiente attivo.", operator_action=True, output=tail)]
    return [_result("tests_failed", "Test automatici", "red", "La suite pytest ha rilevato errori.", blocking=True, output=tail, returncode=completed.returncode)]


def determine_status(checks: Iterable[CheckResult]) -> str:
    checks_list = list(checks)
    if any(item.status == "red" or item.blocking for item in checks_list):
        return "red"
    if any(item.status == "orange" or item.operator_action for item in checks_list):
        return "orange"
    return "green"


def run_update_readiness_check(
    repository: str | os.PathLike[str] | None = None,
    *,
    runner: Runner = _run,
    run_tests: bool = True,
    save_report: bool = True,
) -> ReadinessReport:
    repo = Path(repository or Path.cwd()).resolve()
    checks: list[CheckResult] = []
    checks.extend(_check_repository(repo, runner))
    if not any(item.blocking and item.code in {"repo_missing", "repo_invalid"} for item in checks):
        checks.extend(_check_git_state(repo, runner))
        checks.extend(_check_dependencies(repo))
        checks.extend(_check_environment(repo))
        if run_tests:
            checks.extend(_check_tests(repo, runner))

    status = determine_status(checks)
    report = ReadinessReport(
        status=status,
        ready_for_update=status == "green",
        timestamp=datetime.now(timezone.utc).isoformat(),
        repository=str(repo),
        checks=checks,
    )

    if save_report:
        target = repo / "workspace" / "update-readiness"
        target.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path = target / f"readiness-{stamp}.json"
        report.report_path = str(path)
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def format_summary(report: ReadinessReport) -> str:
    icons = {"green": "[VERDE]", "orange": "[ARANCIONE]", "red": "[ROSSO]"}
    lines = [f"{icons[report.status]} Stato aggiornamento: {report.status.upper()}"]
    for item in report.checks:
        lines.append(f"- {icons[item.status]} {item.title}: {item.message}")
    if report.report_path:
        lines.append(f"Rapporto: {report.report_path}")
    return "\n".join(lines)
