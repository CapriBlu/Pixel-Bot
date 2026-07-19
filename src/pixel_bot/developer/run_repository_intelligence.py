from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .repository_intelligence import RepositoryIntelligence


def main() -> int:
    parser = argparse.ArgumentParser(description="PB-033 Repository Intelligence")
    parser.add_argument("goal", nargs="?", default="Consolidare automaticamente il repository prima del prossimo aggiornamento")
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-openai", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = RepositoryIntelligence(root).run(args.goal, use_openai=not args.no_openai)
    output_dir = root / "workspace" / "repository-intelligence"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"pb033-{stamp}.json"
    latest = output_dir / "latest-result.json"
    text = json.dumps(result, indent=2, ensure_ascii=False)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    print("PB-033 REPOSITORY INTELLIGENCE")
    print("================================")
    print(f"Stato: {result['state']}")
    print(f"OpenAI usato: {'SI' if result['openai_used'] else 'NO'}")
    print(f"File aggiunti automaticamente allo staging: {len(result['staged_automatically'])}")
    for path in result["staged_automatically"]:
        print(f"- {path}")
    pending = [d for d in result["decisions"] if d["action"] in {"ask", "inspect"}]
    if pending:
        print("Elementi ancora ambigui:")
        for item in pending:
            print(f"- {item['path']}: {item['reason']}")
    print(f"Test: {'SUPERATI' if result['tests']['return_code'] == 0 else 'FALLITI'}")
    print(f"Report: {output}")
    return 1 if result["state"] == "ROSSO" else 0


if __name__ == "__main__":
    raise SystemExit(main())
