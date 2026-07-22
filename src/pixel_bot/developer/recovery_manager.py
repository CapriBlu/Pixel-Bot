from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RecoveryAction(StrEnum):
    RETRY_STEP = "retry_step"
    RELOAD_CHECKPOINT = "reload_checkpoint"
    ABORT = "abort"
    REQUEST_HUMAN = "request_human"


@dataclass(slots=True)
class RecoveryDecision:
    action: RecoveryAction
    reason: str


@dataclass(slots=True)
class RecoveryManager:
    request_human_after: int = 3

    def decide(self, error_type: str, attempt: int, max_attempts: int) -> RecoveryDecision:
        if error_type == "watchdog_timeout":
            return RecoveryDecision(RecoveryAction.RELOAD_CHECKPOINT, "loop non responsivo")
        if attempt < max_attempts:
            return RecoveryDecision(RecoveryAction.RETRY_STEP, "tentativi disponibili")
        if attempt >= self.request_human_after:
            return RecoveryDecision(RecoveryAction.REQUEST_HUMAN, "limite di affidabilità raggiunto")
        return RecoveryDecision(RecoveryAction.ABORT, "nessun recupero sicuro disponibile")
