from __future__ import annotations

import argparse
import json
from pathlib import Path

from .openai_state_bridge import OpenAIStateBridge
from .state_collector import StateCollector
from .state_sanitizer import sanitize_state


def main() -> int:
    parser = argparse.ArgumentParser(description="PB-032 OpenAI State Bridge")
    parser.add_argument("goal", nargs="?", default="Analizzare lo stato del repository e indicare il prossimo passo sicuro")
    parser.add_argument("--root", default=".")
    parser.add_argument("--local-only", action="store_true", help="Genera lo State Package senza chiamare OpenAI")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output_dir = root / "workspace" / "openai-state-bridge"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.local_only:
        payload = sanitize_state(StateCollector(root).collect(args.goal))
        result = {"status": "local_only", "state": payload}
    else:
        result = OpenAIStateBridge(root).analyze(args.goal)

    output = output_dir / "latest-result.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
