from __future__ import annotations

import json

from pixel_bot.magi.council import MagiCouncil
from pixel_bot.magi.models import MagiProposal
from pixel_bot.magi.providers import build_default_providers
from pixel_bot.magi.reporting import write_decision_report


def test_write_decision_report(tmp_path):
    decision = MagiCouncil(build_default_providers()).deliberate(
        MagiProposal(goal="Correggere un warning con un micro-intervento reversibile e test")
    )
    destination = tmp_path / "reports" / "decision.json"

    result = write_decision_report(decision, destination)

    assert result == destination
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["proposal"]["goal"]
    assert len(payload["opinions"]) == 3
    assert payload["metadata"]["dry_run"] is True
