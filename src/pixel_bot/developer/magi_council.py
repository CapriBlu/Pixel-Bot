from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


class MagiRole(StrEnum):
    STRATEGIST = "strategist"
    CRITIC = "critic"
    GUARDIAN = "guardian"


class MagiDecision(StrEnum):
    APPROVE = "approve"
    APPROVE_WITH_CHANGES = "approve_with_changes"
    REJECT = "reject"
    VETO = "veto"
    ABSTAIN = "abstain"


class CouncilStatus(StrEnum):
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"
    REJECTED = "rejected"
    HUMAN_CONFIRMATION_REQUIRED = "human_confirmation_required"
    INCONCLUSIVE = "inconclusive"


@dataclass(slots=True)
class MagiContext:
    proposal_id: str
    objective: str
    proposal: str
    evidence: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MagiVote:
    role: MagiRole
    decision: MagiDecision
    confidence: float
    risk: str
    reason: str
    required_changes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve essere compresa tra 0 e 1")
        self.risk = self.risk.strip().lower() or "unknown"
        self.reason = self.reason.strip()


@dataclass(slots=True)
class MagiCouncilPolicy:
    approval_threshold: float = 0.60
    minimum_confidence: float = 0.55
    guardian_veto_enabled: bool = True
    require_all_roles: bool = True
    low_confidence_requires_human: bool = True

    def __post_init__(self) -> None:
        for name, value in {
            "approval_threshold": self.approval_threshold,
            "minimum_confidence": self.minimum_confidence,
        }.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} deve essere compreso tra 0 e 1")


@dataclass(slots=True)
class MagiCouncilReport:
    proposal_id: str
    objective: str
    status: CouncilStatus
    consensus: float
    average_confidence: float
    highest_risk: str
    final_reason: str
    required_changes: list[str]
    votes: list[MagiVote]
    evaluated_at: str

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        for vote in data["votes"]:
            vote["role"] = vote["role"].value if hasattr(vote["role"], "value") else vote["role"]
            vote["decision"] = vote["decision"].value if hasattr(vote["decision"], "value") else vote["decision"]
        return data


MagiEvaluator = Callable[[MagiContext], MagiVote]


@dataclass(slots=True)
class MagiAgent:
    role: MagiRole
    evaluator: MagiEvaluator
    name: str = ""

    def evaluate(self, context: MagiContext) -> MagiVote:
        vote = self.evaluator(context)
        if vote.role != self.role:
            raise ValueError(
                f"L'agente {self.role.value} ha restituito un voto per {vote.role.value}"
            )
        return vote


class MagiCouncil:
    """Consulta agenti indipendenti e produce una decisione tracciabile.

    Gli agenti ricevono lo stesso contesto ma non i voti degli altri. Questo
    limita l'effetto gregge e rende il giudizio utile per scegliere i futuri
    aggiornamenti del progetto.
    """

    _RISK_ORDER = {"unknown": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    _SCORES = {
        MagiDecision.APPROVE: 1.0,
        MagiDecision.APPROVE_WITH_CHANGES: 0.65,
        MagiDecision.ABSTAIN: 0.5,
        MagiDecision.REJECT: 0.0,
        MagiDecision.VETO: 0.0,
    }

    def __init__(
        self,
        agents: Iterable[MagiAgent],
        policy: MagiCouncilPolicy | None = None,
        report_path: Path | None = None,
    ) -> None:
        self.agents = list(agents)
        self.policy = policy or MagiCouncilPolicy()
        self.report_path = report_path
        roles = [agent.role for agent in self.agents]
        if len(roles) != len(set(roles)):
            raise ValueError("Ogni ruolo MAGI può comparire una sola volta")
        if self.policy.require_all_roles:
            missing = set(MagiRole) - set(roles)
            if missing:
                raise ValueError(f"Ruoli MAGI mancanti: {sorted(role.value for role in missing)}")

    def deliberate(self, context: MagiContext) -> MagiCouncilReport:
        if not context.proposal_id.strip():
            raise ValueError("proposal_id non può essere vuoto")
        if not context.objective.strip():
            raise ValueError("objective non può essere vuoto")
        if not context.proposal.strip():
            raise ValueError("proposal non può essere vuoto")

        votes = [agent.evaluate(context) for agent in self.agents]
        consensus = self._weighted_consensus(votes)
        average_confidence = sum(vote.confidence for vote in votes) / len(votes)
        highest_risk = self._highest_risk(votes)
        required_changes = self._deduplicate(
            change for vote in votes for change in vote.required_changes if change.strip()
        )
        status, reason = self._decide(votes, consensus, average_confidence, required_changes)
        report = MagiCouncilReport(
            proposal_id=context.proposal_id,
            objective=context.objective,
            status=status,
            consensus=round(consensus, 4),
            average_confidence=round(average_confidence, 4),
            highest_risk=highest_risk,
            final_reason=reason,
            required_changes=required_changes,
            votes=votes,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._write_report(report)
        return report

    def rank_proposals(self, contexts: Iterable[MagiContext]) -> list[MagiCouncilReport]:
        reports = [self.deliberate(context) for context in contexts]
        status_order = {
            CouncilStatus.APPROVED: 4,
            CouncilStatus.REVISION_REQUIRED: 3,
            CouncilStatus.HUMAN_CONFIRMATION_REQUIRED: 2,
            CouncilStatus.INCONCLUSIVE: 1,
            CouncilStatus.REJECTED: 0,
        }
        return sorted(
            reports,
            key=lambda item: (
                status_order[item.status],
                item.consensus,
                item.average_confidence,
                -self._RISK_ORDER.get(item.highest_risk, 0),
            ),
            reverse=True,
        )

    def _decide(
        self,
        votes: list[MagiVote],
        consensus: float,
        average_confidence: float,
        required_changes: list[str],
    ) -> tuple[CouncilStatus, str]:
        guardian = next((vote for vote in votes if vote.role == MagiRole.GUARDIAN), None)
        if (
            self.policy.guardian_veto_enabled
            and guardian is not None
            and guardian.decision == MagiDecision.VETO
        ):
            return (
                CouncilStatus.HUMAN_CONFIRMATION_REQUIRED,
                f"Veto del Guardiano: {guardian.reason or 'azione ad alto rischio'}",
            )

        rejects = sum(vote.decision in {MagiDecision.REJECT, MagiDecision.VETO} for vote in votes)
        if rejects >= 2:
            return CouncilStatus.REJECTED, "La maggioranza dei MAGI ha respinto la proposta"

        if average_confidence < self.policy.minimum_confidence:
            if self.policy.low_confidence_requires_human:
                return (
                    CouncilStatus.HUMAN_CONFIRMATION_REQUIRED,
                    "Confidenza media insufficiente: serve una decisione umana",
                )
            return CouncilStatus.INCONCLUSIVE, "Confidenza media insufficiente"

        changes_requested = any(
            vote.decision == MagiDecision.APPROVE_WITH_CHANGES for vote in votes
        ) or bool(required_changes)
        if consensus >= self.policy.approval_threshold:
            if changes_requested:
                return (
                    CouncilStatus.REVISION_REQUIRED,
                    "Proposta valida, ma deve essere aggiornata prima dell'esecuzione",
                )
            return CouncilStatus.APPROVED, "Consenso MAGI raggiunto"

        return CouncilStatus.INCONCLUSIVE, "Consenso insufficiente per una decisione autonoma"

    def _weighted_consensus(self, votes: list[MagiVote]) -> float:
        weight = sum(vote.confidence for vote in votes)
        if weight == 0:
            return 0.0
        return sum(self._SCORES[vote.decision] * vote.confidence for vote in votes) / weight

    def _highest_risk(self, votes: list[MagiVote]) -> str:
        return max(
            (vote.risk for vote in votes),
            key=lambda risk: self._RISK_ORDER.get(risk, self._RISK_ORDER["unknown"]),
            default="unknown",
        )

    @staticmethod
    def _deduplicate(items: Iterable[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            normalized = item.strip()
            key = normalized.casefold()
            if normalized and key not in seen:
                seen.add(key)
                result.append(normalized)
        return result

    def _write_report(self, report: MagiCouncilReport) -> None:
        if self.report_path is None:
            return
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.report_path.with_suffix(self.report_path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(report.as_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.report_path)


def build_rule_based_magi() -> list[MagiAgent]:
    """Crea tre MAGI deterministici utilizzabili senza provider AI esterno.

    È un fallback sicuro e testabile. In seguito ogni evaluator potrà essere
    sostituito con un provider LLM mantenendo invariato il contratto MagiVote.
    """

    def strategist(context: MagiContext) -> MagiVote:
        has_goal = len(context.objective.split()) >= 2
        has_evidence = bool(context.evidence)
        decision = MagiDecision.APPROVE if has_goal and has_evidence else MagiDecision.APPROVE_WITH_CHANGES
        changes = [] if has_evidence else ["Aggiungere evidenze o test misurabili"]
        return MagiVote(
            role=MagiRole.STRATEGIST,
            decision=decision,
            confidence=0.82 if has_evidence else 0.68,
            risk="low",
            reason="La proposta è coerente con l'obiettivo" if has_goal else "Obiettivo poco definito",
            required_changes=changes,
            tags=["utility", "roadmap"],
        )

    def critic(context: MagiContext) -> MagiVote:
        has_tests = any("test" in item.casefold() for item in context.evidence + context.constraints)
        decision = MagiDecision.APPROVE if has_tests else MagiDecision.APPROVE_WITH_CHANGES
        return MagiVote(
            role=MagiRole.CRITIC,
            decision=decision,
            confidence=0.86,
            risk="medium" if not has_tests else "low",
            reason="Criteri di verifica presenti" if has_tests else "Mancano criteri di verifica espliciti",
            required_changes=[] if has_tests else ["Definire test di accettazione"],
            tags=["quality"],
        )

    def guardian(context: MagiContext) -> MagiVote:
        text = " ".join([context.proposal, *context.constraints]).casefold()
        critical_terms = ("cancella", "pagamento", "password", "invia automaticamente", "irreversibile")
        critical = any(term in text for term in critical_terms)
        return MagiVote(
            role=MagiRole.GUARDIAN,
            decision=MagiDecision.VETO if critical else MagiDecision.APPROVE,
            confidence=0.93,
            risk="critical" if critical else "low",
            reason="Rilevata azione critica o irreversibile" if critical else "Nessun rischio critico rilevato",
            required_changes=["Richiedere conferma umana tramite Safety Gate"] if critical else [],
            tags=["safety"],
        )

    return [
        MagiAgent(MagiRole.STRATEGIST, strategist, "MELCHIOR"),
        MagiAgent(MagiRole.CRITIC, critic, "BALTHASAR"),
        MagiAgent(MagiRole.GUARDIAN, guardian, "CASPAR"),
    ]
