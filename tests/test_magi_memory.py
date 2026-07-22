from __future__ import annotations

from pixel_bot.magi.memory import MagiMemoryStore
from pixel_bot.magi.models import DecisionStatus, MagiOpinion, MagiRole


def test_memory_is_separate_per_role(tmp_path):
    store = MagiMemoryStore(tmp_path)
    opinion = MagiOpinion(
        role=MagiRole.MELCHIOR,
        status=DecisionStatus.REVISE,
        summary="Serve una metrica.",
        alternative="Aggiungere una baseline.",
        confidence=0.9,
    )

    store.append(
        role=MagiRole.MELCHIOR,
        proposal_goal="Migliorare il progetto",
        opinion=opinion,
        final_status=DecisionStatus.REVISE,
    )

    assert len(store.load(MagiRole.MELCHIOR)) == 1
    assert store.load(MagiRole.BALTHASAR) == ()
    assert store.path_for(MagiRole.MELCHIOR).name == "melchior.jsonl"


def test_memory_limit_returns_recent_entries(tmp_path):
    store = MagiMemoryStore(tmp_path)
    for index in range(3):
        opinion = MagiOpinion(
            role=MagiRole.CASPAR,
            status=DecisionStatus.APPROVE,
            summary=f"Scelta {index}",
            confidence=0.8,
        )
        store.append(
            role=MagiRole.CASPAR,
            proposal_goal=f"Goal {index}",
            opinion=opinion,
            final_status=DecisionStatus.APPROVE,
        )

    entries = store.load(MagiRole.CASPAR, limit=2)

    assert [entry.proposal_goal for entry in entries] == ["Goal 1", "Goal 2"]
