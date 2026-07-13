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
    "paint": "mspaint.exe