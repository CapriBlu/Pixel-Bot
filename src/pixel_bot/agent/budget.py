from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BudgetState:
    max_requests: int = 10
    max_estimated_cost: float = 0.50
    estimated_cost_per_request: float = 0.01
    requests_used: int = 0
    estimated_cost_used: float = 0.0

    def ensure_available(self) -> None:
        if self.requests_used >= self.max_requests:
            raise RuntimeError("Limite massimo di richieste AI raggiunto.")
        next_cost = self.estimated_cost_used + self.estimated_cost_per_request
        if next_cost > self.max_estimated_cost:
            raise RuntimeError("Budget AI stimato esaurito.")

    def record_request(self) -> None:
        self.ensure_available()
        self.requests_used += 1
        self.estimated_cost_used = round(
            self.estimated_cost_used + self.estimated_cost_per_request,
            6,
        )

    def to_dict(self) -> dict[str, int | float]:
        return {
            "max_requests": self.max_requests,
            "requests_used": self.requests_used,
            "max_estimated_cost": self.max_estimated_cost,
            "estimated_cost_used": self.estimated_cost_used,
            "estimated_cost_per_request": self.estimated_cost_per_request,
        }
