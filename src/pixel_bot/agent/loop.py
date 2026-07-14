from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pixel_bot.agent.memory import AgentMemory
from pixel_bot.agent.models import AgentDecision
from pixel_bot.agent.workspace import Workspace
from pixel_bot.core.executor import execute_action
from pixel_bot.core.safety import Action, validate_action


class DecisionProvider(Protocol):
    def decide(
        self,
        *,
        goal: str,
        screenshot_path: Path,
        history: list[dict[str, Any]],
    ) -> AgentDecision: ...


ConfirmationCallback = Callable[[Action, AgentDecision], bool]
EventCallback = Callable[[str, dict[str, Any]], None]
ScreenshotProvider = Callable[[], Path]
ActionExecutor = Callable[[Action], Any]


def _default_screenshot_provider() -> Path:
    from pixel_bot.vision.screen_capture import capture_screen

    return capture_screen()


@dataclass(slots=True)
class AgentLoopResult:
    status: str
    steps: int
    history: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "steps": self.steps,
            "history": self.history,
            "error": self.error,
            "session_id": self.session_id,
        }


class AgentLoop:
    def __init__(
        self,
        decision_provider: DecisionProvider,
        *,
        max_steps: int = 10,
        confirmation_callback: ConfirmationCallback | None = None,
        event_callback: EventCallback | None = None,
        workspace: Workspace | None = None,
        memory: AgentMemory | None = None,
        screenshot_provider: ScreenshotProvider = _default_screenshot_provider,
        action_executor: ActionExecutor = execute_action,
    ) -> None:
        if max_steps <= 0:
            raise ValueError("max_steps deve essere maggiore di zero.")

        self.decision_provider = decision_provider
        self.max_steps = max_steps
        self.confirmation_callback = confirmation_callback
        self.event_callback = event_callback
        self.workspace = workspace or Workspace()
        self.memory = memory or AgentMemory(self.workspace.memory_path)
        self.screenshot_provider = screenshot_provider
        self.action_executor = action_executor
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()
        self._emit("stop_requested", {})

    def run(self, goal: str) -> AgentLoopResult:
        normalized_goal = goal.strip()
        if not normalized_goal:
            raise ValueError("L'obiettivo non può essere vuoto.")

        self._stop_event.clear()
        self.workspace.initialize()
        self.memory.load()
        history = self.memory.recent(limit=50)
        steps = 0

        self.workspace.append_event("run_started", {"goal": normalized_goal})
        self._emit("run_started", {"goal": normalized_goal})

        try:
            while steps < self.max_steps:
                if self._stop_event.is_set():
                    return self._finish("stopped", steps, history)

                screenshot_path = self.screenshot_provider()
                decision = self.decision_provider.decide(
                    goal=normalized_goal,
                    screenshot_path=screenshot_path,
                    history=history.copy(),
                )

                decision_record = {
                    "step": steps + 1,
                    "screenshot": str(screenshot_path),
                    "decision": decision.to_dict(),
                }
                self.workspace.append_event("decision_created", decision_record)
                self._emit("decision_created", decision_record)

                if decision.completed:
                    history.append(decision_record)
                    self.memory.append(decision_record)
                    return self._finish("completed", steps, history)

                action = decision.to_action()
                validate_action(action)

                if self.confirmation_callback is not None:
                    approved = self.confirmation_callback(action, decision)
                    if not approved:
                        decision_record["status"] = "rejected"
                        history.append(decision_record)
                        self.memory.append(decision_record)
                        return self._finish("rejected", steps, history)

                result = self.action_executor(action)
                steps += 1
                decision_record.update(
                    {
                        "status": "executed",
                        "action": {
                            "name": action.name,
                            "parameters": action.parameters.copy(),
                        },
                        "result": result,
                    }
                )
                history.append(decision_record)
                self.memory.append(decision_record)
                self.workspace.append_event("action_executed", decision_record)
                self._emit("action_executed", decision_record)

            return self._finish("max_steps_reached", steps, history)

        except Exception as error:
            self.workspace.append_event("run_failed", {"error": str(error)})
            return self._finish("failed", steps, history, error=str(error))

    def _finish(
        self,
        status: str,
        steps: int,
        history: list[dict[str, Any]],
        *,
        error: str | None = None,
    ) -> AgentLoopResult:
        result = AgentLoopResult(
            status=status,
            steps=steps,
            history=history,
            error=error,
            session_id=self.workspace.session_id,
        )
        self.workspace.append_event("run_finished", result.to_dict())
        self.workspace.save_summary(result.to_dict())
        self._emit("run_finished", result.to_dict())
        return result

    def _emit(self, name: str, payload: dict[str, Any]) -> None:
        if self.event_callback is not None:
            self.event_callback(name, payload)
