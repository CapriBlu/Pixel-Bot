from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .council import MagiCouncil
from .memory import MagiMemoryStore
from .models import MagiProposal, MagiRole
from .providers import build_default_providers
from .reporting import write_decision_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pixelbot-magi",
        description="MAGI dry-run deliberation engine for Pixel Bot.",
    )
    parser.add_argument("--goal", required=True, help="Obiettivo da valutare.")
    parser.add_argument("--context", default="", help="Contesto della proposta.")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", required=True)
    parser.add_argument(
        "--memory-dir",
        default="workspace/magi-memory",
        help="Cartella delle memorie individuali MAGI.",
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=20,
        help="Numero massimo di ricordi recenti letti per membro.",
    )
    parser.add_argument(
        "--no-memory-write",
        action="store_true",
        help="Legge la memoria ma non registra la deliberazione corrente.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.dry_run:
        raise SystemExit("MAGI v0.2 consente esclusivamente --dry-run.")
    if args.memory_limit < 0:
        raise SystemExit("--memory-limit deve essere >= 0.")

    memory_store = MagiMemoryStore(args.memory_dir)
    memories = {
        role: memory_store.load(role, limit=args.memory_limit) for role in MagiRole
    }

    proposal = MagiProposal(
        goal=args.goal.strip(),
        context=args.context.strip(),
        evidence=tuple(item.strip() for item in args.evidence if item.strip()),
        constraints=tuple(item.strip() for item in args.constraint if item.strip()),
    )
    decision = MagiCouncil(build_default_providers(memories)).deliberate(proposal)
    report_path = write_decision_report(decision, Path(args.report))

    if not args.no_memory_write:
        for opinion in decision.opinions:
            memory_store.append(
                role=opinion.role,
                proposal_goal=proposal.goal,
                opinion=opinion,
                final_status=decision.status,
            )

    output = {
        "status": decision.status.value,
        "recommended_action": decision.recommended_action,
        "requires_creator_review": decision.requires_creator_review,
        "report": str(report_path),
        "memory_dir": str(memory_store.root),
        "memory_written": not args.no_memory_write,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
