import json
from pathlib import Path

from safety import Action


def load_task(task_path: str) -> list[Action]:
    path = Path(task_path)

    if not path.exists():
        raise FileNotFoundError(f"Task non trovato: {path}")

    with path.open("r", encoding="utf-8-sig") as file:
        task_data = json.load(file)

    if not isinstance(task_data, list):
        raise ValueError("Il file del task deve contenere una lista di azioni.")

    actions = []

    for index, item in enumerate(task_data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Azione {index} non valida.")

        name = item.get("name")
        parameters = item.get("parameters", {})

        if not isinstance(name, str):
            raise ValueError(f"Nome dell'azione {index} non valido.")

        if not isinstance(parameters, dict):
            raise ValueError(f"Parametri dell'azione {index} non validi.")

        actions.append(
            Action(
                name=name,
                parameters=parameters,
            )
        )

    return actions
