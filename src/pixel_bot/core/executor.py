import subprocess
import time

from pixel_bot.automation.keyboard_controller import press_key, write_text
from pixel_bot.automation.mouse_controller import click_mouse, move_mouse
from pixel_bot.core.logger import get_logger
from pixel_bot.core.safety import Action, ALLOWED_APPS, validate_action
from pixel_bot.vision.screen_capture import capture_screen
from pixel_bot.vision.window_controller import focus_window


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

    if action.name == "focus_window":
        window = focus_window(
            action.parameters["title"],
            action.parameters.get("timeout", 5.0),
        )

        return window.title

    raise RuntimeError(f"Azione non gestita: {action.name}")
