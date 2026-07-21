from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(slots=True)
class SelfAnalysisReport:
    total_events: int
    retries: int
    failures: int
    watchdog_interventions: int
    dominant_failure: str
    recommendations: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SelfAnalysisEngine:
    def analyze(self, events: Iterable[dict[str, Any]]) -> SelfAnalysisReport:
        rows = list(events)
        types = Counter(str(row.get("type", "unknown")) for row in rows)
        errors = Counter(
            str(row.get("payload", {}).get("error_type", ""))
            for row in rows
            if row.get("payload", {}).get("error_type")
        )
        retries = types["step_retry_scheduled"]
        watchdog = errors["watchdog_timeout"]
        failures = sum(value for key, value in errors.items() if key)
        rec: list[str] = []
        if retries > 0:
            rec.append("Analizzare gli step con retry e rendere più specifiche esecuzione e verifica.")
        if watchdog > 0:
            rec.append("Isolare le operazioni bloccanti in un processo separato con timeout forzabile.")
        if failures == 0:
            rec.append("Nessun errore classificato: mantenere i test di regressione correnti.")
        dominant = errors.most_common(1)[0][0] if errors else "none"
        return SelfAnalysisReport(len(rows), retries, failures, watchdog, dominant, rec)
