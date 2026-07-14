from pathlib import Path

from pixel_bot.agent.loop import AgentLoop
from pixel_bot.agent.models import AgentDecision
from pixel_bot.agent.workspace import Workspace


class SequenceProvider:
    def __init__(self, decisions):
        self.decisions = iter(decisions)

    def decide(self, *, goal, screenshot_path, history):
        return next(self.decisions)


def test_agent_loop_executes_action_and_completes(tmp_path):
    provider = SequenceProvider(
        [
            AgentDecision(
                observation="Desktop",
                reasoning_summary="Attendere",
                completed=False,
                action_name="wait",
                action_parameters={"seconds": 0},
            ),
            AgentDecision(
                observation="Operazione conclusa",
                reasoning_summary="Completato",
                completed=True,
            ),
        ]
    )
    executed = []
    workspace = Workspace(root=tmp_path / "workspace")

    loop = AgentLoop(
        provider,
        workspace=workspace,
        screenshot_provider=lambda: Path("screen.png"),
        action_executor=lambda action: executed.append(action.name) or "ok",
    )

    result = loop.run("Completa il test")

    assert result.status == "completed"
    assert result.steps == 1
    assert executed == ["wait"]
    assert workspace.summary_path.exists()
    assert workspace.events_path.exists()


def test_agent_loop_stops_at_max_steps(tmp_path):
    decision = AgentDecision(
        observation="Desktop",
        reasoning_summary="Attendere",
        completed=False,
        action_name="wait",
        action_parameters={"seconds": 0},
    )
    provider = SequenceProvider([decision, decision])

    loop = AgentLoop(
        provider,
        max_steps=2,
        workspace=Workspace(root=tmp_path / "workspace"),
        screenshot_provider=lambda: Path("screen.png"),
        action_executor=lambda action: None,
    )

    result = loop.run("Esegui due passi")

    assert result.status == "max_steps_reached"
    assert result.steps == 2


def test_agent_loop_respects_rejection(tmp_path):
    provider = SequenceProvider(
        [
            AgentDecision(
                observation="Desktop",
                reasoning_summary="Aprire applicazione",
                completed=False,
                action_name="open_app",
                action_parameters={"app": "notepad"},
            )
        ]
    )

    loop = AgentLoop(
        provider,
        workspace=Workspace(root=tmp_path / "workspace"),
        confirmation_callback=lambda action, decision: False,
        screenshot_provider=lambda: Path("screen.png"),
        action_executor=lambda action: None,
    )

    result = loop.run("Apri Blocco note")

    assert result.status == "rejected"
    assert result.steps == 0
