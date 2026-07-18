from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any


@dataclass(slots=True)
class FailureRegistry:
    """Registro semplice per i fallimenti di test/usabilità usato dal Developer Agent.

    Problema risolto:
    - In precedenza la classe usava dataclass(slots=True) ma init/\n    __post_init__ assegnavano attributi non dichiarati, causando
    AttributeError all'istanziazione. Dichiarando esplicitamente
    gli attributi (anche quelli inizializzati in __post_init__) la
    classe è compatibile con slots.

    L'istanza calcola e crea la directory workspace/test-failure-registry
    e mantiene un file JSON (failures.json) con le voci registrate.
    """

    workspace: Path
    name: str = "test-failure-registry"
    # attributi dichiarati per essere compatibili con dataclass(slots=True)
    path: Path = field(init=False)
    index_file: Path = field(init=False)

    def __post_init__(self) -> None:
        # Normalizza workspace a Path e calcola il percorso della registry
        self.workspace = Path(self.workspace)
        self.path = (self.workspace / self.name).resolve()
        # Assicura che la directory esista
        self.path.mkdir(parents=True, exist_ok=True)
        # File JSON che contiene l'elenco dei failure
        self.index_file = self.path / "failures.json"
        if not self.index_file.exists():
            # inizializza con una lista vuota
            self.index_file.write_text("[]", encoding="utf-8")

    def register(self, item: Any) -> None:
        """Registra un oggetto (serializzabile JSON) nel file dei failure."""
        data = self._load()
        data.append(item)
        self.index_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def all(self) -> list[Any]:
        """Restituisce la lista di tutte le voci registrate."""
        return self._load()

    def clear(self) -> None:
        """Svuota il registro dei failure."""
        self.index_file.write_text("[]", encoding="utf-8")

    def _load(self) -> list[Any]:
        if not self.index_file.exists():
            return []
        try:
            return json.loads(self.index_file.read_text(encoding="utf-8"))
        except Exception:
            # In caso di file malformato, sovrascrive con lista vuota per coerenza
            self.index_file.write_text("[]", encoding="utf-8")
            return []
