from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class ClassifiedPath:
    status: str
    path: str
    category: str
    confidence: str
    reason: str
    suggested_action: str


SAFE_BACKUP_SUFFIXES = (".pixelbot.bak",)
PROJECT_PREFIXES = ("src/", "tests/", "launcher/", "docs/")
PROJECT_FILES = {
    "pyproject.toml",
    "pytest.ini",
    "requirements.txt",
    "README.md",
    ".gitignore",
    "CREA_PIXEL_BOT_APP.cmd",
    "PixelBot.ico",
    "PixelBotApp.cs",
}
LOCAL_PATTERNS = (
    ".tmp",
    ".log",
    ".swp",
    "~",
)


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def parse_porcelain(lines: Iterable[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        status = line[:2]
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"')
        parsed.append((status, path))
    return parsed


def classify(status: str, path: str) -> ClassifiedPath:
    normalized = path.replace("\\", "/")
    lower = normalized.lower()

    if lower.endswith(SAFE_BACKUP_SUFFIXES):
        return ClassifiedPath(
            status,
            normalized,
            "backup_residuo",
            "alta",
            "Backup automatico Pixel Bot presente dentro il working tree.",
            "Spostare in workspace/update-backups; azione sicura e reversibile.",
        )

    if normalized.startswith(PROJECT_PREFIXES) or normalized in PROJECT_FILES:
        return ClassifiedPath(
            status,
            normalized,
            "componente_progetto",
            "alta",
            "Percorso appartenente al codice, ai test, alla documentazione o al launcher.",
            "Revisionare e includere nel commit di consolidamento se la modifica e intenzionale.",
        )

    if lower.endswith((".png", ".jpg", ".jpeg", ".ico")):
        return ClassifiedPath(
            status,
            normalized,
            "asset_da_verificare",
            "media",
            "File grafico: potrebbe essere un asset dell'app oppure un file locale.",
            "Verificare utilizzo nel codice; poi includere o spostare fuori dal repository.",
        )

    if normalized.startswith("workspace/") or any(lower.endswith(p) for p in LOCAL_PATTERNS):
        return ClassifiedPath(
            status,
            normalized,
            "artefatto_locale",
            "alta",
            "File generato localmente o temporaneo.",
            "Non committare; mantenere in un percorso ignorato da Git.",
        )

    if lower.endswith((".cmd", ".ps1")):
        return ClassifiedPath(
            status,
            normalized,
            "automazione_da_verificare",
            "media",
            "Script operativo non ancora classificato.",
            "Verificare se e parte stabile del progetto oppure uno strumento locale.",
        )

    return ClassifiedPath(
        status,
        normalized,
        "da_revisionare",
        "bassa",
        "Nessuna regola affidabile ha classificato automaticamente il file.",
        "Richiede decisione prima di commit, ignore o spostamento.",
    )


def analyze(repo: Path) -> dict:
    status_result = run_git(repo, "status", "--porcelain=v1")
    if status_result.returncode != 0:
        raise RuntimeError(status_result.stderr.strip() or "Impossibile leggere git status")

    entries = [classify(status, path) for status, path in parse_porcelain(status_result.stdout.splitlines())]
    head = run_git(repo, "rev-parse", "HEAD")
    branch = run_git(repo, "branch", "--show-current")
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.category] = counts.get(entry.category, 0) + 1

    return {
        "schema_version": 1,
        "timestamp": datetime.now().astimezone().isoformat(),
        "repository": str(repo),
        "branch": branch.stdout.strip() if branch.returncode == 0 else None,
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "dirty": bool(entries),
        "counts": counts,
        "entries": [asdict(entry) for entry in entries],
    }


def move_safe_backups(repo: Path, report: dict) -> list[dict[str, str]]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination_root = repo / "workspace" / "update-backups" / f"pb030-{timestamp}"
    moved: list[dict[str, str]] = []

    for entry in report["entries"]:
        if entry["category"] != "backup_residuo":
            continue
        source = repo / entry["path"]
        if not source.exists() or not source.is_file():
            continue
        destination = destination_root / entry["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        moved.append({"source": entry["path"], "destination": str(destination.relative_to(repo)).replace("\\", "/")})
    return moved


def write_reports(repo: Path, report: dict, moved: list[dict[str, str]]) -> tuple[Path, Path]:
    output = repo / "workspace" / "repository-consolidation"
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report["safe_actions_applied"] = moved
    report["remaining_after_safe_actions"] = analyze(repo)["entries"] if moved else report["entries"]

    json_path = output / f"consolidation-{stamp}.json"
    txt_path = output / f"consolidation-{stamp}.txt"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "PB-030 - CONSOLIDAMENTO REPOSITORY",
        "===================================",
        f"Repository: {report['repository']}",
        f"Branch: {report.get('branch')}",
        f"Commit: {report.get('head')}",
        f"File inizialmente da classificare: {len(report['entries'])}",
        f"Azioni sicure applicate: {len(moved)}",
        "",
    ]
    if moved:
        lines.append("AZIONI SICURE ESEGUITE")
        lines.append("----------------------")
        for item in moved:
            lines.append(f"- Spostato {item['source']} -> {item['destination']}")
        lines.append("")

    lines.extend(["CLASSIFICAZIONE", "---------------"])
    for index, entry in enumerate(report["entries"], start=1):
        lines.extend(
            [
                f"{index}. [{entry['category'].upper()}] {entry['path']}",
                f"   Stato Git: {entry['status']}",
                f"   Confidenza: {entry['confidence']}",
                f"   Motivo: {entry['reason']}",
                f"   Azione: {entry['suggested_action']}",
                "",
            ]
        )

    remaining = report["remaining_after_safe_actions"]
    lines.extend(
        [
            "RISULTATO",
            "---------",
            f"File ancora da decidere: {len(remaining)}",
            "Il modulo non esegue commit, push, delete o ignore automatici.",
            "Le modifiche ambigue richiedono classificazione prima del prossimo aggiornamento.",
            "",
            f"Report JSON: {json_path}",
            f"Report leggibile: {txt_path}",
        ]
    )
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, txt_path


def main() -> int:
    parser = argparse.ArgumentParser(description="PB-030 Repository Consolidation Assistant")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--apply-safe", action="store_true", help="Sposta solo i backup .pixelbot.bak in workspace/update-backups")
    args = parser.parse_args()

    repo = args.repo.resolve()
    report = analyze(repo)
    moved = move_safe_backups(repo, report) if args.apply_safe else []
    json_path, txt_path = write_reports(repo, report, moved)

    remaining = report["remaining_after_safe_actions"]
    print("=" * 60)
    print("PB-030 - RISULTATO CONSOLIDAMENTO")
    print("=" * 60)
    print(f"Azioni sicure applicate: {len(moved)}")
    print(f"File ancora da classificare: {len(remaining)}")
    print(f"Report: {txt_path}")
    print(f"JSON: {json_path}")
    if remaining:
        print("STATO: ARANCIONE - nessun errore tecnico, decisioni ancora necessarie")
    else:
        print("STATO: VERDE - working tree pulito")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
