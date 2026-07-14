from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pixel_bot.developer.agent import DeveloperAgent
from pixel_bot.developer.models import FileChange
from pixel_bot.developer.task_loader import TaskLoader


def _load_changes(path: Path) -> list[FileChange]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Il file delle modifiche deve contenere una lista JSON.")
    changes: list[FileChange] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Ogni modifica deve essere un oggetto JSON.")
        file_path = item.get("path")
        content = item.get("content")
        if not isinstance(file_path, str) or not isinstance(content, str):
            raise ValueError("Ogni modifica richiede path e content testuali.")
        changes.append(
            FileChange(
                path=file_path,
                content=content,
                reason=str(item.get("reason", "")),
            )
        )
    return changes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pixel Bot Developer Agent")
    parser.add_argument("task", type=Path, help="Task JSON da eseguire")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Root repository")
    parser.add_argument("--changes", type=Path, help="File JSON con modifiche proposte")
    parser.add_argument("--apply", action="store_true", help="Applica le modifiche e lancia i test")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("workspace/developer-report.json"),
        help="Percorso del report JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository_root = args.repo.resolve()
    task = TaskLoader(args.task.parent).load(args.task)
    changes = _load_changes(args.changes) if args.changes else []
    agent = DeveloperAgent(repository_root)
    result = agent.run(
        task,
        change_provider=(lambda task, snapshot, plan: changes),
        apply_changes=args.apply,
        report_path=(repository_root / args.report).resolve()
        if not args.report.is_absolute()
        else args.report,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status in {"ready_for_review", "changes_proposed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
