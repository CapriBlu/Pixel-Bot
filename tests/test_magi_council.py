import json

import pytest

from pixel_bot.developer.magi_council import (
    CouncilStatus,
    MagiAgent,
    MagiContext,
    MagiCouncil,
    MagiCouncilPolicy,
    MagiDecision,
    MagiRole,
    MagiVote,
    build_rule_based_magi,
)


def vote(role, decision, confidence=0.9, risk="low", changes=None):
    return MagiVote(
        role=role,
        decision=decision,
        confidence=confidence,
        risk=risk,
        reason=f"{role.value}: {decision.value}",
        required_changes=changes or [],
    )


def council_with(decisions, **policy):
    agents = []
    for role, decision in decisions.items():
        agents.append(MagiAgent(role, lambda ctx, r=role, d=decision: vote(r, d)))
    return MagiCouncil(agents, MagiCouncilPolicy(**policy))


def context(proposal="Aggiungere un report con test"):
    return MagiContext("PB-040", "Scegliere il prossimo miglioramento", proposal, evidence=["test automatici"])


def test_three_approvals_are_approved():
    council = council_with({role: MagiDecision.APPROVE for role in MagiRole})
    result = council.deliberate(context())
    assert result.status == CouncilStatus.APPROVED
    assert result.consensus == 1.0


def test_guardian_veto_requires_human_confirmation():
    council = council_with({
        MagiRole.STRATEGIST: MagiDecision.APPROVE,
        MagiRole.CRITIC: MagiDecision.APPROVE,
        MagiRole.GUARDIAN: MagiDecision.VETO,
    })
    result = council.deliberate(context("Invia automaticamente una password"))
    assert result.status == CouncilStatus.HUMAN_CONFIRMATION_REQUIRED
    assert "Guardiano" in result.final_reason


def test_two_rejections_reject_proposal():
    council = council_with({
        MagiRole.STRATEGIST: MagiDecision.REJECT,
        MagiRole.CRITIC: MagiDecision.REJECT,
        MagiRole.GUARDIAN: MagiDecision.APPROVE,
    })
    assert council.deliberate(context()).status == CouncilStatus.REJECTED


def test_changes_create_revision_required():
    agents = [
        MagiAgent(MagiRole.STRATEGIST, lambda c: vote(MagiRole.STRATEGIST, MagiDecision.APPROVE)),
        MagiAgent(MagiRole.CRITIC, lambda c: vote(MagiRole.CRITIC, MagiDecision.APPROVE_WITH_CHANGES, changes=["Aggiungere test"])),
        MagiAgent(MagiRole.GUARDIAN, lambda c: vote(MagiRole.GUARDIAN, MagiDecision.APPROVE)),
    ]
    result = MagiCouncil(agents).deliberate(context())
    assert result.status == CouncilStatus.REVISION_REQUIRED
    assert result.required_changes == ["Aggiungere test"]


def test_low_confidence_requires_human():
    agents = [MagiAgent(role, lambda c, r=role: vote(r, MagiDecision.APPROVE, confidence=0.2)) for role in MagiRole]
    result = MagiCouncil(agents).deliberate(context())
    assert result.status == CouncilStatus.HUMAN_CONFIRMATION_REQUIRED


def test_missing_role_is_rejected():
    with pytest.raises(ValueError, match="mancanti"):
        MagiCouncil([MagiAgent(MagiRole.STRATEGIST, lambda c: vote(MagiRole.STRATEGIST, MagiDecision.APPROVE))])


def test_duplicate_role_is_rejected():
    with pytest.raises(ValueError, match="una sola volta"):
        MagiCouncil([
            MagiAgent(MagiRole.STRATEGIST, lambda c: vote(MagiRole.STRATEGIST, MagiDecision.APPROVE)),
            MagiAgent(MagiRole.STRATEGIST, lambda c: vote(MagiRole.STRATEGIST, MagiDecision.APPROVE)),
        ], MagiCouncilPolicy(require_all_roles=False))


def test_agent_cannot_impersonate_other_role():
    agent = MagiAgent(MagiRole.STRATEGIST, lambda c: vote(MagiRole.CRITIC, MagiDecision.APPROVE))
    with pytest.raises(ValueError, match="restituito"):
        agent.evaluate(context())


def test_report_is_written_atomically(tmp_path):
    path = tmp_path / "magi-report.json"
    council = council_with({role: MagiDecision.APPROVE for role in MagiRole})
    council.report_path = path
    result = council.deliberate(context())
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["status"] == result.status.value
    assert len(saved["votes"]) == 3


def test_rule_based_magi_requests_tests_when_missing():
    council = MagiCouncil(build_rule_based_magi())
    result = council.deliberate(MagiContext("x", "Valutare proposta", "Aggiungere cache"))
    assert result.status == CouncilStatus.REVISION_REQUIRED
    assert "Definire test di accettazione" in result.required_changes


def test_rule_based_guardian_vetoes_critical_action():
    council = MagiCouncil(build_rule_based_magi())
    result = council.deliberate(MagiContext("x", "Valutare proposta", "Cancella file irreversibile", evidence=["test"] ))
    assert result.status == CouncilStatus.HUMAN_CONFIRMATION_REQUIRED
    assert result.highest_risk == "critical"


def test_rank_proposals_places_approved_first():
    council = MagiCouncil(build_rule_based_magi())
    approved = MagiContext("good", "Valutare proposta", "Aggiungere telemetria", evidence=["test automatici"])
    revision = MagiContext("rev", "Valutare proposta", "Aggiungere cache")
    ranked = council.rank_proposals([revision, approved])
    assert ranked[0].proposal_id == "good"
    assert ranked[0].status == CouncilStatus.APPROVED


def test_confidence_validation():
    with pytest.raises(ValueError, match="confidence"):
        vote(MagiRole.CRITIC, MagiDecision.APPROVE, confidence=1.2)
