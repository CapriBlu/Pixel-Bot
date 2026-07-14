from __future__ import annotations

import subprocess
import time
from typing import Any

from pixel_bot.core.logger import get_logger
from pixel_bot.core.safety import ALLOWED_APPS, Action, validate_action

logger = get_logger(__name__)


def capture_screen():
    from pixel_bot.vision.screen_capture import capture_screen as implementation

    return implementation()


def move_mouse(x: int, y: int, duration: float = 0.5):
    from pixel_bot.automation.mouse_controller import move_mouse as implementation

    return implementation(x, y, duration)


def click_mouse(x: int, y: int):
    from pixel_bot.automation.mouse_controller import click_mouse as implementation

    return implementation(x, y)


def write_text(text: str, interval: float = 0.03):
    from pixel_bot.automation.keyboard_controller import write_text as implementation

    return implementation(text, interval)


def press_key(key: str):
    from pixel_bot.automation.keyboard_controller import press_key as implementation

    return implementation(key)


def focus_window(title: str, timeout: float = 5.0):
    from pixel_bot.vision.window_controller import focus_window as implementation

    return implementation(title, timeout)


def execute_action(action: Action) -> Any:
    """Execute one validated desktop action.

    GUI-dependent modules are imported lazily so that the package and its tests
    remain usable on headless systems and CI runners.
    """
    validate_action(action)
    logger.info("Esecuzione azione=%s parametri=%s", action.name, action.parameters)

    if action.name == "screenshot":
        return capture_screen()

    if action.name == "move_mouse":
        move_mouse(
            action.parameters["x"],
            action.parameters["y"],
            action.parameters.get("duration", 0.5),
        )
        return None

    if action.name == "click":
        click_mouse(action.parameters["x"], action.parameters["y"])
        return None

    if action.name == "write_text":
        write_text(
            action.parameters["text"],
            action.parameters.get("interval", 0.03),
        )
        return None

    if action.name == "press_key":
        press_key(action.parameters["key"])
        return None

    if action.name == "wait":
        time.sleep(action.parameters.get("seconds", 1))
        return None

    if action.name == "open_app":
        app_name = action.parameters["app"]
        executable = ALLOWED_APPS[app_name]
        subprocess.Popen([executable])
        return executable

    if action.name == "focus_window":
        window = focus_window(
            action.parameters["title"],
            action.parameters.get("timeout", 5.0),
        )
        return window.title

    raise RuntimeError(f"Azione non gestita: {action.name}")
