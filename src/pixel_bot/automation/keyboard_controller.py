import pyautogui


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2


def write_text(text: str, interval: float = 0.03) -> None:
    pyautogui.write(text, interval=interval)


def press_key(key: str) -> None:
    pyautogui.press(key)


def hotkey(*keys: str) -> None:
    pyautogui.hotkey(*keys)
