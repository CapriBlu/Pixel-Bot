from __future__ import annotations

from collections.abc import Callable

from .memory import MagiMemoryEntry
from .models import DecisionStatus, MagiOpinion, MagiProposal, MagiRole

OpinionProvider = Callable[[MagiProposal, tuple[MagiOpinion, ...]], MagiOpinion]


def _has_term(proposal: MagiProposal, *terms: str) -> bool:
    haystack = " ".join(
        [proposal.goal, proposal.context, *proposal.evidence, *proposal.constraints]
    ).casefold()
    return any(term.casefold() in haystack for term in terms)


def _memory_note(memory: tuple[MagiMemoryEntry, ...]) -> str:
    if not memory:
        return ""
    failures = sum(entry.outcome == "failed" for entry in memory)
    corrections = sum(
        entry.status in {DecisionStatus.REVISE, DecisionStatus.REJECT}
        for entry in memory
    )
    return (
        f" Storico recente: {len(memory)} decisioni, "
        f"{corrections} correzioni, {failures} esiti falliti."
    )


def build_melchior_provider(
    memory: tuple[MagiMemoryEntry, ...] = (),
) -> OpinionProvider:
    def provider(
        proposal: MagiProposal, peer_opinions: tuple[MagiOpinion, ...]
    ) -> MagiOpinion:
        second_round = bool(peer_opinions)
        conditions = (
            "Definire un criterio misurabile prima dell'implementazione.",
            "Eseguire i test pertinenti prima e dopo la modifica.",
        )

        if not proposal.goal.strip():
            return MagiOpinion(
                role=MagiRole.MELCHIOR,
                status=DecisionStatus.REJECT,
                summary="La proposta non contiene un obiettivo tecnico verificabile.",
                risks=("Impossibile misurare il miglioramento.",),
                alternative="Formulare un unico obiettivo tecnico, limitato e verificabile.",
                conditions=conditions,
                confidence=0.98,
            )

        lacks_measurement = not _has_term(
            proposal,
            "misur",
            "criterio",
            "test",
            "benchmark",
            "metrica",
            "verific",
        )
        if lacks_measurement:
            return MagiOpinion(
                role=MagiRole.MELCHIOR,
                status=DecisionStatus.REVISE,
                summary=(
                    "Il valore tecnico non è ancora dimostrabile."
                    + _memory_note(memory)
                ),
                risks=("Il cambiamento potrebbe sembrare utile senza produrre evidenza.",),
                objections=("Manca una misura esplicita del successo.",),
                alternative="Aggiungere una metrica, una baseline e un test di accettazione.",
                conditions=conditions,
                confidence=0.92,
            )

        summary = (
            "La proposta è tecnicamente valutabile dopo il confronto."
            if second_round
            else "La proposta è tecnicamente valutabile e misurabile."
        )
        return MagiOpinion(
            role=MagiRole.MELCHIOR,
            status=DecisionStatus.APPROVE,
            summary=summary + _memory_note(memory),
            benefits=("Produce conoscenza verificabile sul sistema.",),
            conditions=conditions,
            confidence=0.86,
        )

    return provider


def build_balthasar_provider(
    memory: tuple[MagiMemoryEntry, ...] = (),
) -> OpinionProvider:
    def provider(
        proposal: MagiProposal, peer_opinions: tuple[MagiOpinion, ...]
    ) -> MagiOpinion:
        high_risk = _has_term(
            proposal,
            "autonomia",
            "automatico",
            "architettura",
            "database",
            "sicurezza",
            "main",
            "delete",
            "rimuovere",
            "riscrivere",
        )
        missing_rollback = not _has_term(
            proposal,
            "rollback",
            "reversibile",
            "backup",
            "dry-run",
            "micro-intervento",
        )
        recent_failures = sum(entry.outcome == "failed" for entry in memory)

        if (high_risk and missing_rollback) or recent_failures >= 2:
            reason = (
                "La proposta espone fondamenta stabili senza una ritirata esplicita."
                if high_risk and missing_rollback
                else "Lo storico recente mostra troppi esiti falliti per procedere senza protezioni."
            )
            return MagiOpinion(
                role=MagiRole.BALTHASAR,
                status=DecisionStatus.REVISE,
                summary=reason + _memory_note(memory),
                risks=(
                    "Regressione non protetta.",
                    "Aumento del bisogno di correzioni manuali.",
                ),
                objections=("Manca una strategia di rollback verificabile.",),
                alternative=(
                    "Ridurre la modifica a un dry-run o a un micro-intervento reversibile, "
                    "aggiungendo test e rollback prima dell'applicazione."
                ),
                conditions=(
                    "Conservare il comportamento pubblico esistente.",
                    "Preparare rollback o backup.",
                    "Bloccare l'applicazione se i test falliscono.",
                ),
                confidence=0.95,
            )

        return MagiOpinion(
            role=MagiRole.BALTHASAR,
            status=DecisionStatus.APPROVE,
            summary=(
                "Il rischio è accettabile entro confini, test e arresto sicuro."
                + _memory_note(memory)
            ),
            benefits=("Le fondamenta rimangono protette.",),
            risks=("Rischi residui da verificare con la suite completa.",),
            conditions=(
                "Non modificare file estranei.",
                "Mantenere una via di rollback.",
                "Fermarsi al primo test fallito.",
            ),
            confidence=0.89,
        )

    return provider


def build_caspar_provider(
    memory: tuple[MagiMemoryEntry, ...] = (),
) -> OpinionProvider:
    def provider(
        proposal: MagiProposal, peer_opinions: tuple[MagiOpinion, ...]
    ) -> MagiOpinion:
        too_broad = _has_term(
            proposal,
            "tutto",
            "completo",
            "intero",
            "molti moduli",
            "nuovo framework",
            "riscrivere",
        )
        objections = tuple(
            opinion.summary
            for opinion in peer_opinions
            if opinion.status in {DecisionStatus.REVISE, DecisionStatus.REJECT}
        )
        historical_revisions = sum(
            entry.status in {DecisionStatus.REVISE, DecisionStatus.REJECT}
            for entry in memory
        )

        if too_broad or objections or historical_revisions >= 3:
            return MagiOpinion(
                role=MagiRole.CASPAR,
                status=DecisionStatus.REVISE,
                summary=(
                    "Il cambiamento merita di avanzare, ma con una strada più corta."
                    + _memory_note(memory)
                ),
                benefits=("Mantiene il valore strategico riducendo tempi e superficie.",),
                risks=("Una scorciatoia non validata potrebbe spostare il problema.",),
                objections=objections,
                alternative=(
                    "Realizzare prima il minimo incremento end-to-end che dimostri il valore, "
                    "poi estenderlo soltanto sulla base delle misurazioni."
                ),
                conditions=(
                    "Una sola capacità per commit.",
                    "Criterio di successo esplicito.",
                    "Nessuna espansione prima della verifica.",
                ),
                confidence=0.90,
            )

        return MagiOpinion(
            role=MagiRole.CASPAR,
            status=DecisionStatus.APPROVE,
            summary=(
                "La proposta è abbastanza concentrata da produrre avanzamento reale."
                + _memory_note(memory)
            ),
            benefits=("Trasforma l'obiettivo in progresso concreto.",),
            risks=("Il valore strategico deve essere verificato dopo il primo incremento.",),
            conditions=(
                "Preferire il percorso con meno file e dipendenze.",
                "Concludere con una raccomandazione per il passo successivo.",
            ),
            confidence=0.84,
        )

    return provider


def build_default_providers(
    memories: dict[MagiRole, tuple[MagiMemoryEntry, ...]] | None = None,
) -> dict[MagiRole, OpinionProvider]:
    memories = memories or {}
    return {
        MagiRole.MELCHIOR: build_melchior_provider(
            memories.get(MagiRole.MELCHIOR, ())
        ),
        MagiRole.BALTHASAR: build_balthasar_provider(
            memories.get(MagiRole.BALTHASAR, ())
        ),
        MagiRole.CASPAR: build_caspar_provider(
            memories.get(MagiRole.CASPAR, ())
        ),
    }
