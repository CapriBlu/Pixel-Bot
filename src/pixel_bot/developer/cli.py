from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pixel_bot.agent.ai_client import AIClientConfig
from pixel_bot.agent.workspace import Workspace
from pixel_bot.developer.agent import DeveloperAgent
from pixel_bot.developer.ai_provider import DeveloperAIProvider
from pixel_bot.developer.models import FileChange
from pixel_bot.developer.task_loader import TaskLoader
from pixel_bot.developer.task_queue import TaskQueue


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
    parser.add_argument("task", type=Path, nargs="?", help="Task JSON da eseguire")
    parser.add_argument(
        "--next-task",
        action="store_true",
        help="Seleziona automaticamente il prossimo task pendente dalla cartella tasks",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=Path("tasks"),
        help="Cartella della task queue, relativa al repository",
    )
    parser.add_argument(
        "--queue-state",
        type=Path,
        default=Path("workspace/developer-task-state.json"),
        help="File persistente con stato e tentativi della task queue",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Numero massimo di tentativi per task nella coda",
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Root repository")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--changes", type=Path, help="File JSON con modifiche proposte")
    source.add_argument(
        "--ai",
        action="store_true",
        help="Genera le modifiche tramite il backend AI configurato nell'ambiente",
    )
    parser.add_argument(
        "--simulation-changes",
        type=Path,
        help="Modifiche programmate da usare con --ai e PIXEL_BOT_DRY_RUN=1",
    )
    parser.add_argument("--apply", action="store_true", help="Applica le modifiche e lancia i test")
    parser.add_argument("--commit", action="store_true", help="Crea un commit Git dopo test verdi")
    parser.add_argument("--push", action="store_true", help="Esegue push della branch di task")
    parser.add_argument("--open-pr", action="store_true", help="Apre una Pull Request draft tramite gh")
    parser.add_argument("--pr-base", default="main", help="Branch base della Pull Request")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("workspace/developer-report.json"),
        help="Percorso del report JSON",
    )
    return parser


def _build_change_provider(args: argparse.Namespace, repository_root: Path):
    if args.ai:
        config = AIClientConfig.from_environment()
        simulated_changes = None
        if args.simulation_changes is not None:
            if not config.dry_run:
                raise ValueError("--simulation-changes richiede PIXEL_BOT_DRY_RUN=1.")
            simulated_changes = [[*_load_changes(args.simulation_changes)]]
        workspace = Workspace(repository_root / "workspace")
        workspace.initialize()
        return DeveloperAIProvider(
            repository_root=repository_root,
            config=config,
            workspace=workspace,
            simulated_changes=simulated_changes,
        )

    if args.simulation_changes is not None:
        raise ValueError("--simulation-changes può essere usato solo insieme a --ai.")

    changes = _load_changes(args.changes) if args.changes else []
    return lambda task, snapshot, plan: changes


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (args.commit or args.push or args.open_pr) and not args.apply:
        raise SystemExit("--commit, --push e --open-pr richiedono --apply.")

    repository_root = args.repo.resolve()
    if args.next_task == (args.task is not None):
        raise SystemExit("Specificare esattamente un task oppure --next-task.")

    queue = None
    queued = None
    if args.next_task:
        tasks_dir = args.tasks_dir if args.tasks_dir.is_absolute() else repository_root / args.tasks_dir
        state_path = args.queue_state if args.queue_state.is_absolute() else repository_root / args.queue_state
        queue = TaskQueue(tasks_dir, state_path, max_attempts=args.max_attempts)
        queued = queue.next_task()
        if queued is None:
            print(json.dumps({"status": "queue_empty"}, ensure_ascii=False, indent=2))
            return 0
        queue.mark_started(queued)
        task = queued.task
    else:
        assert args.task is not None
        task = TaskLoader(args.task.parent).load(args.task)

    provider = _build_change_provider(args, repository_root)
    agent = DeveloperAgent(repository_root)
    result = agent.run(
        task,
        change_provider=provider,
        apply_changes=args.apply,
        report_path=(repository_root / args.report).resolve()
        if not args.report.is_absolute()
        else args.report,
        commit=args.commit or args.push or args.open_pr,
        push=args.push or args.open_pr,
        open_pr=args.open_pr,
        pr_base=args.pr_base,
    )
    successful = result.status in {
        "ready_for_review",
        "changes_proposed",
        "committed",
        "pull_request_opened",
    }
    if queue is not None and queued is not None:
        if successful:
            queue.mark_completed(queued, args.report)
        else:
            queue.mark_failed(queued, result.error or result.status)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
