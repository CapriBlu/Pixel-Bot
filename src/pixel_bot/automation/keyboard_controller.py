import time

import pyautogui


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2


def write_text(text: str, interval: float = 0.03) -> None:
    pyautogui.write(text, interval=interval)


def press_key(key: str, presses: int = 1, interval: float = 0.05) -> None:
    pyautogui.press(key, presses=presses, interval=interval)


def hotkey(*keys: str) -> None:
    pyautogui.hotkey(*keys)


def key_down(key: str) -> None:
    pyautogui.keyDown(key)


def key_up(key: str) -> None:
    pyautogui.keyUp(key)


def hold_key(key: str, seconds: float) -> None:
    key_down(key)
    try:
        time.sleep(seconds)
    finally:
        key_up(key)
