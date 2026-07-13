import subprocess
import time

from keyboard_controller import press_key, write_text
from logger import get_logger
from mouse_controller import click_mouse, move_mouse
from safety import Action, ALLOWED_APPS, validate_action
from screen_capture import capture_screen


logger = get_logger(__name__)


def execute_action(action: Action):
    validate_action(action)

    logger.info(
        "Esecuzione azione=%s parametri=%s",
        action.name,
        action.parameters,
    )

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
        click_mouse(
            action.parameters["x"],
            action.parameters["y"],
        )
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

    raise RuntimeError(f"Azione non gestita: {action.name}")
