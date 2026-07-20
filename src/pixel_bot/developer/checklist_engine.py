from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable


class ChecklistStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"


@dataclass(slots=True)
class ChecklistItem:
    id: int
    text: str
    status: ChecklistStatus = ChecklistStatus.PENDING
    evidence: list[str] = field(default_factory=list)

    def complete(self, evidence: str | None = None) -> None:
        self.status = ChecklistStatus.COMPLETED
        if evidence:
            self.evidence.append(evidence)

    def mark_running(self) -> None:
        self.status = ChecklistStatus.RUNNING

    def mark_unavailable(self, reason: str | None = None) -> None:
        self.status = ChecklistStatus.UNAVAILABLE
        if reason:
            self.evidence.append(reason)


_NUMBERED = re.compile(r"^\s*(?:[-*]\s*)?(\d+)[.)-]\s+(.+?)\s*$")
_CHECKBOX = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s+(.+?)\s*$")


class Checklist:
    def __init__(self, items: Iterable[ChecklistItem] = ()) -> None:
        self.items = list(items)

    @classmethod
    def from_text(cls, text: str) -> "Checklist":
        items: list[ChecklistItem] = []
        next_id = 1
        for line in text.splitlines():
            numbered = _NUMBERED.match(line)
            if numbered:
                item_id = int(numbered.group(1))
                items.append(ChecklistItem(item_id, numbered.group(2)))
                next_id = max(next_id, item_id + 1)
                continue
            checkbox = _CHECKBOX.match(line)
            if checkbox:
                status = ChecklistStatus.COMPLETED if checkbox.group(1).lower() == "x" else ChecklistStatus.PENDING
                items.append(ChecklistItem(next_id, checkbox.group(2), status=status))
                next_id += 1
        return cls(items)

    def get(self, item_id: int) -> ChecklistItem:
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(item_id)

    @property
    def is_complete(self) -> bool:
        return bool(self.items) and all(item.status in {ChecklistStatus.COMPLETED, ChecklistStatus.UNAVAILABLE} for item in self.items)

    @property
    def remaining(self) -> list[ChecklistItem]:
        return [item for item in self.items if item.status not in {ChecklistStatus.COMPLETED, ChecklistStatus.UNAVAILABLE}]

    def as_dict(self) -> dict:
        return {
            "complete": self.is_complete,
            "items": [
                {"id": i.id, "text": i.text, "status": i.status.value, "evidence": list(i.evidence)}
                for i in self.items
            ],
        }
