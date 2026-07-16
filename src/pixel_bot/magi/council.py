from __future__ import annotations

from collections.abc import Callable

from .models import DecisionStatus, MagiDecision, MagiOpinion, MagiProposal, MagiRole

OpinionProvider = Callable[[MagiProposal, tuple[MagiOpinion, ...]], MagiOpinion]


class MagiCouncil:
    """Coordinate independent MAGI evaluations and build a safe synthesis.

    The first implementation is intentionally provider-agnostic. Providers may be
    deterministic functions in tests or AI-backed adapters in later milestones.
    The council never modifies repository files.
    """

    def __init__(self, providers: dict[MagiRole, OpinionProvider]) -> None:
        missing = set(MagiRole) - set(providers)
        if missing:
            names = ", ".join(sorted(role.value for role in missing))
            raise ValueError(f"missing MAGI providers: {names}")
        self._providers = dict(providers)

    def deliberate(self, proposal: MagiProposal) -> MagiDecision:
        independent = tuple(
            self._validate_opinion(role, self._providers[role](proposal, ()))
            for role in MagiRole
        )

        challenged = tuple(
            self._validate_opinion(
                role,
                self._providers[role](
                    proposal,
                    tuple(opinion for opinion in independent if opinion.role != role),
                ),
            )
            for role in MagiRole
        )

        return self._synthesise(proposal, challenged)

    @staticmethod
    def _validate_opinion(expected_role: MagiRole, opinion: MagiOpinion) -> MagiOpinion:
        if opinion.role != expected_role:
            raise ValueError(
                f"provider for {expected_role.value} returned {opinion.role.value}"
            )
        if opinion.status in {DecisionStatus.REVISE, DecisionStatus.REJECT} and not (
            opinion.alternative or opinion.conditions
        ):
            raise ValueError(
                f"{opinion.role.value} criticism must include an alternative or conditions"
            )
        return opinion

    @staticmethod
    def _synthesise(
        proposal: MagiProposal, opinions: tuple[MagiOpinion, ...]
    ) -> MagiDecision:
        statuses = {opinion.status for opinion in opinions}
        all_conditions = tuple(
            dict.fromkeys(
                condition
                for opinion in opinions
                for condition in opinion.conditions
                if condition
            )
        )

        if DecisionStatus.ESCALATE in statuses:
            status = DecisionStatus.ESCALATE
            creator_review = True
        elif DecisionStatus.REJECT in statuses:
            status = DecisionStatus.REVISE
            creator_review = True
        elif DecisionStatus.REVISE in statuses:
            status = DecisionStatus.REVISE
            creator_review = False
        elif DecisionStatus.DEFER in statuses:
            status = DecisionStatus.DEFER
            creator_review = False
        else:
            status = DecisionStatus.APPROVE
            creator_review = False

        alternatives = [opinion.alternative for opinion in opinions if opinion.alternative]
        recommended_action = alternatives[-1] if alternatives else proposal.goal
        synthesis = " | ".join(
            f"{opinion.role.value}: {opinion.summary}" for opinion in opinions
        )

        return MagiDecision(
            proposal=proposal,
            opinions=opinions,
            status=status,
            synthesis=synthesis,
            recommended_action=recommended_action,
            required_conditions=all_conditions,
            requires_creator_review=creator_review,
            metadata={"deliberation_rounds": 2, "dry_run": True},
        )
