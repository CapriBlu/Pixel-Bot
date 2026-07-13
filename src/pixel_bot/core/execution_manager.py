import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pixel_bot.core.executor import execute_action
from pixel_bot.core.planner import Plan
from pixel_bot.core.safety import Action


EventCallback = Callable[[str, Any], None]


@dataclass
class ExecutionState:
    status: str = "idle"
    current_step: int | None = None
    error: str | None = None


class ExecutionManager:
    def __init__(
        self,
        event_callback: EventCallback | None = None,
    ) -> None:
        self.event_callback = event_callback
        self.state = ExecutionState()

        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self.state.status == "running"

    def start(self, plan: Plan) -> None:
        with self._lock:
            if self.is_running:
                raise RuntimeError(
                    "È già presente un piano in esecuzione."
                )

            if plan.status not in {"ready", "draft"}:
                raise ValueError(
                    f"Il piano non può essere avviato: {plan.status}"
                )

            self._stop_event.clear()

            self.state = ExecutionState(
                status="running",
                current_step=None,
                error=None,
            )

            plan.status = "running"

            self._worker = threading.Thread(
                target=self._run_plan,
                args=(plan,),
                daemon=True,
            )

            self._worker.start()

        self._emit("execution_started", plan)

    def stop(self) -> None:
        if not self.is_running:
            return

        self._stop_event.set()
        self._emit("stop_requested", None)

    def wait(self, timeout: float | None = None) -> None:
        worker = self._worker

        if worker is not None:
            worker.join(timeout=timeout)

    def _run_plan(self, plan: Plan) -> None:
        try:
            for step in plan.steps:
                if self._stop_event.is_set():
                    step.status = "stopped"
                    plan.status = "stopped"
                    self.state.status = "stopped"

                    self._emit(
                        "step_updated",
                        {
                            "step_id": step.id,
                            "status": step.status,
                        },
                    )

                    self._emit("execution_stopped", plan)
                    return

                self.state.current_step = step.id
                step.status = "running"

                self._emit(
                    "step_updated",
                    {
                        "step_id": step.id,
                        "status": step.status,
                    },
                )

                self._emit(
                    "log",
                    {
                        "message": (
                            f"Esecuzione {step.action} "
                            f"{step.parameters}"
                        )
                    },
                )

                action = Action(
                    name=step.action,
                    parameters=step.parameters.copy(),
                )

                result = execute_action(action)

                step.status = "completed"

                self._emit(
                    "step_updated",
                    {
                        "step_id": step.id,
                        "status": step.status,
                    },
                )

                if result is not None:
                    self._emit(
                        "action_result",
                        {
                            "step_id": step.id,
                            "result": result,
                        },
                    )

            plan.status = "completed"

            self.state.status = "completed"
            self.state.current_step = None

            self._emit("execution_completed", plan)

        except Exception as error:
            plan.status = "failed"

            self.state.status = "failed"
            self.state.error = str(error)

            self._emit(
                "execution_failed",
                {
                    "plan": plan,
                    "error": str(error),
                },
            )

    def _emit(self, name: str, payload: Any) -> None:
        if self.event_callback is not None:
            self.event_callback(name, payload)