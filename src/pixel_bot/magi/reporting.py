from __future__ import annotations

import json
from pathlib import Path

from .models import MagiDecision


def write_decision_report(decision: MagiDecision, path: str | Path) -> Path:
    """Write a UTF-8 JSON report atomically and return its final path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    payload = json.dumps(decision.to_dict(), ensure_ascii=False, indent=2) + "\n"
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(destination)
    return destination
