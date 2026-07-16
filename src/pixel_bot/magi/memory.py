from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import DecisionStatus, MagiOpinion, MagiRole


@dataclass(slots=True, frozen=True)
class MagiMemoryEntry:
    timestamp: str
    role: MagiRole
    proposal_goal: str
    status: DecisionStatus
    summary: str
    alternative: str
    conditions: tuple[str, ...]
    confidence: float
    final_status: DecisionStatus
    outcome: str = "unknown"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        data["status"] = self.status.value
        data["final_status"] = self.final_status.value
        data["conditions"] = list(self.conditions)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MagiMemoryEntry":
        return cls(
            timestamp=str(data["timestamp"]),
            role=MagiRole(data["role"]),
            proposal_goal=str(data["proposal_goal"]),
            status=DecisionStatus(data["status"]),
            summary=str(data.get("summary", "")),
            alternative=str(data.get("alternative", "")),
            conditions=tuple(data.get("conditions", ())),
            confidence=float(data.get("confidence", 0.0)),
            final_status=DecisionStatus(data["final_status"]),
            outcome=str(data.get("outcome", "unknown")),
            notes=str(data.get("notes", "")),
        )


class MagiMemoryStore:
    """Persist separate append-only decision histories for each MAGI member."""

    def __init__(self, root: str | Path = "workspace/magi-memory") -> None:
        self.root = Path(root)

    def path_for(self, role: MagiRole) -> Path:
        return self.root / f"{role.value}.jsonl"

    def append(
        self,
        *,
        role: MagiRole,
        proposal_goal: str,
        opinion: MagiOpinion,
        final_status: DecisionStatus,
        outcome: str = "unknown",
        notes: str = "",
    ) -> MagiMemoryEntry:
        if opinion.role != role:
            raise ValueError("opinion role does not match memory role")

        entry = MagiMemoryEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            role=role,
            proposal_goal=proposal_goal,
            status=opinion.status,
            summary=opinion.summary,
            alternative=opinion.alternative,
            conditions=opinion.conditions,
            confidence=opinion.confidence,
            final_status=final_status,
            outcome=outcome,
            notes=notes,
        )
        path = self.path_for(role)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return entry

    def load(self, role: MagiRole, *, limit: int | None = None) -> tuple[MagiMemoryEntry, ...]:
        path = self.path_for(role)
        if not path.exists():
            return ()

        entries = tuple(
            MagiMemoryEntry.from_dict(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if limit is None:
            return entries
        if limit < 0:
            raise ValueError("limit must be >= 0")
        return entries[-limit:] if limit else ()

    def summarize(self, role: MagiRole, *, limit: int = 10) -> dict[str, Any]:
        entries = self.load(role, limit=limit)
        by_status: dict[str, int] = {}
        by_outcome: dict[str, int] = {}
        for entry in entries:
            by_status[entry.status.value] = by_status.get(entry.status.value, 0) + 1
            by_outcome[entry.outcome] = by_outcome.get(entry.outcome, 0) + 1

        return {
            "role": role.value,
            "entries_considered": len(entries),
            "status_counts": by_status,
            "outcome_counts": by_outcome,
            "recent_goals": [entry.proposal_goal for entry in entries],
        }
