from pathlib import Path

import pytest

from pixel_bot.agent.ai_client import AIClient, AIClientConfig
from pixel_bot.agent.models import AgentDecision
from pixel_bot.agent.workspace import Workspace


def test_dry_run_uses_programmed_decision_and_records_budget(tmp_path):
    workspace = Workspace(root=tmp_path / "workspace")
    decision = AgentDecision("desktop", "done", True)
    client = AIClient(
        AIClientConfig(dry_run=True, max_requests_per_task=2),
        workspace=workspace,
        simulated_decisions=[decision],
    )

    result = client.decide(goal="test", screenshot_path=Path("missing.png"), history=[])

    assert result.completed is True
    assert client.request_count == 1
    assert workspace.recent_events()[-1]["event"] == "ai_request"


def test_budget_blocks_extra_requests():
    client = AIClient(AIClientConfig(dry_run=True, max_requests_per_task=1))
    client.decide(goal="test", screenshot_path=Path("x"), history=[])

    with pytest.raises(RuntimeError, match="Limite massimo"):
        client.decide(goal="test", screenshot_path=Path("x"), history=[])


def test_transport_response_is_validated(tmp_path):
    screenshot = tmp_path / "screen.png"
    screenshot.write_bytes(b"png")
    client = AIClient(
        AIClientConfig(endpoint="https://example.invalid"),
        transport=lambda request, timeout: {
            "decision": {
                "observation": "desktop",
                "reasoning_summary": "complete",
                "completed": True,
                "action": None,
            }
        },
    )

    assert client.decide(goal="test", screenshot_path=screenshot, history=[]).completed
