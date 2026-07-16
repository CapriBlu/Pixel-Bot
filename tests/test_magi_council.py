from pixel_bot.magi import (
    DecisionStatus,
    MagiCouncil,
    MagiOpinion,
    MagiProposal,
    MagiRole,
)


def _provider(role: MagiRole, status: DecisionStatus, *, alternative: str = ""):
    def evaluate(proposal: MagiProposal, peers: tuple[MagiOpinion, ...]) -> MagiOpinion:
        phase = "challenge" if peers else "independent"
        return MagiOpinion(
            role=role,
            status=status,
            summary=f"{phase} evaluation for {proposal.goal}",
            alternative=alternative,
            conditions=("run tests",) if status == DecisionStatus.REVISE else (),
            confidence=0.8,
        )

    return evaluate


def test_council_approves_when_all_roles_approve() -> None:
    council = MagiCouncil(
        {
            MagiRole.MELCHIOR: _provider(MagiRole.MELCHIOR, DecisionStatus.APPROVE),
            MagiRole.BALTHASAR: _provider(MagiRole.BALTHASAR, DecisionStatus.APPROVE),
            MagiRole.CASPAR: _provider(MagiRole.CASPAR, DecisionStatus.APPROVE),
        }
    )

    decision = council.deliberate(MagiProposal(goal="Improve diagnostics"))

    assert decision.status == DecisionStatus.APPROVE
    assert len(decision.opinions) == 3
    assert decision.metadata["deliberation_rounds"] == 2
    assert decision.metadata["dry_run"] is True


def test_balthasar_revision_forces_constructive_revision() -> None:
    council = MagiCouncil(
        {
            MagiRole.MELCHIOR: _provider(MagiRole.MELCHIOR, DecisionStatus.APPROVE),
            MagiRole.BALTHASAR: _provider(
                MagiRole.BALTHASAR,
                DecisionStatus.REVISE,
                alternative="Apply a smaller reversible patch",
            ),
            MagiRole.CASPAR: _provider(MagiRole.CASPAR, DecisionStatus.APPROVE),
        }
    )

    decision = council.deliberate(MagiProposal(goal="Rewrite the execution engine"))

    assert decision.status == DecisionStatus.REVISE
    assert decision.recommended_action == "Apply a smaller reversible patch"
    assert "run tests" in decision.required_conditions


def test_criticism_without_alternative_is_rejected() -> None:
    council = MagiCouncil(
        {
            MagiRole.MELCHIOR: _provider(MagiRole.MELCHIOR, DecisionStatus.APPROVE),
            MagiRole.BALTHASAR: _provider(MagiRole.BALTHASAR, DecisionStatus.REJECT),
            MagiRole.CASPAR: _provider(MagiRole.CASPAR, DecisionStatus.APPROVE),
        }
    )

    try:
        council.deliberate(MagiProposal(goal="Unsafe proposal"))
    except ValueError as exc:
        assert "alternative or conditions" in str(exc)
    else:
        raise AssertionError("expected constructive-criticism validation to fail")
