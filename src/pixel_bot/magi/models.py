from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class MagiRole(StrEnum):
    MELCHIOR = "melchior"
    BALTHASAR = "balthasar"
    CASPAR = "caspar"


class DecisionStatus(StrEnum):
    APPROVE = "approve"
    REVISE = "revise"
    DEFER = "defer"
    ESCALATE = "escalate"
    REJECT = "reject"


@dataclass(slots=True, frozen=True)
class MagiProposal:
    goal: str
    context: str = ""
    evidence: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class MagiOpinion:
    role: MagiRole
    status: DecisionStatus
    summary: str
    benefits: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    objections: tuple[str, ...] = ()
    alternative: str = ""
    conditions: tuple[str, ...] = ()
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        data["status"] = self.status.value
        return data


@dataclass(slots=True, frozen=True)
class MagiDecision:
    proposal: MagiProposal
    opinions: tuple[MagiOpinion, ...]
    status: DecisionStatus
    synthesis: str
    recommended_action: str
    required_conditions: tuple[str, ...] = ()
    requires_creator_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal": self.proposal.to_dict(),
            "opinions": [opinion.to_dict() for opinion in self.opinions],
            "status": self.status.value,
            "synthesis": self.synthesis,
            "recommended_action": self.recommended_action,
            "required_conditions": list(self.required_conditions),
            "requires_creator_review": self.requires_creator_review,
            "metadata": dict(self.metadata),
        }
