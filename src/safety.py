from dataclasses import dataclass
from typing import Any


ALLOWED_ACTIONS = {
    "screenshot",
    "move_mouse",
    "click",
    "write_text",
    "press_key",
    "wait",
}


@dataclass
class Action:
    name: str
    parameters: dict[str, Any]


def validate_action(action: Action) -> None:
    if action.name not in ALLOWED_ACTIONS:
        raise ValueError(f"Azione non autorizzata: {action.name}")

    if action.name in {"move_mouse", "click"}:
        x = action.parameters.get("x")
        y = action.parameters.get("y")

        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("Le coordinate x e y devono essere numeri interi.")

        if x < 0 or y < 0:
            raise ValueError("Le coordinate non possono essere negative.")

    if action.name == "write_text":
        text = action.parameters.get("text")

        if not isinstance(text, str) or not text:
            raise ValueError("Il testo deve essere una stringa non vuota.")

    if action.name == "wait":
        seconds = action.parameters.get("seconds", 1)

        if not isinstance(seconds, (int, float)):
            raise ValueError("La durata deve essere numerica.")

        if seconds < 0 or seconds > 30:
            raise ValueError("L'attesa deve essere compresa tra 0 e 30 secondi.")
