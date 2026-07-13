from dataclasses import dataclass
from typing import Any


ALLOWED_ACTIONS = {
    "screenshot",
    "move_mouse",
    "click",
    "write_text",
    "press_key",
    "hotkey",
    "wait",
    "open_app",
    "focus_window",
}

ALLOWED_APPS = {
    "notepad": "notepad.exe",
    "blocco note": "notepad.exe",
    "calculator": "calc.exe",
    "calcolatrice": "calc.exe",
    "paint": "mspaint.exe",
    "esplora file": "explorer.exe",
}

ALLOWED_HOTKEY_KEYS = {
    "ctrl",
    "shift",
    "alt",
    "win",
    "tab",
    "enter",
    "esc",
    "a",
    "c",
    "v",
    "x",
    "z",
}


@dataclass
class Action:
    name: str
    parameters: dict[str, Any]


def validate_action(action: Action) -> None:
    if action.name not in ALLOWED_ACTIONS:
        raise ValueError(f"Azione non autorizzata: {action.name}")

    if not isinstance(action.parameters, dict):
        raise ValueError("I parametri dell'azione devono essere un dizionario.")

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

    if action.name == "press_key":
        key = action.parameters.get("key")

        if not isinstance(key, str) or not key:
            raise ValueError("Il tasto deve essere una stringa non vuota.")

    if action.name == "hotkey":
        keys = action.parameters.get("keys")

        if not isinstance(keys, list) or len(keys) < 2:
            raise ValueError("La combinazione deve contenere almeno due tasti.")

        if not all(isinstance(key, str) and key for key in keys):
            raise ValueError("I tasti della combinazione non sono validi.")

        normalized = [key.lower() for key in keys]
        unsupported = [key for key in normalized if key not in ALLOWED_HOTKEY_KEYS]
        if unsupported:
            raise ValueError(
                "Tasti non autorizzati nella combinazione: " + ", ".join(unsupported)
            )

    if action.name == "wait":
        seconds = action.parameters.get("seconds", 1)

        if not isinstance(seconds, (int, float)):
            raise ValueError("La durata deve essere numerica.")

        if seconds < 0 or seconds > 120:
            raise ValueError("L'attesa deve essere compresa tra 0 e 120 secondi.")

    if action.name == "open_app":
        app = action.parameters.get("app")

        if app not in ALLOWED_APPS:
            raise ValueError(f"Applicazione non autorizzata: {app}")

    if action.name == "focus_window":
        title = action.parameters.get("title")
        timeout = action.parameters.get("timeout", 5.0)

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Il titolo della finestra non è valido.")

        if not isinstance(timeout, (int, float)):
            raise ValueError("Il timeout deve essere numerico.")

        if timeout <= 0 or timeout > 30:
            raise ValueError("Il timeout deve essere compreso tra 0 e 30 secondi.")
