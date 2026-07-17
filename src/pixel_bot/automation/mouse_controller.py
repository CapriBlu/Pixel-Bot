import pyautogui


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def get_mouse_position():
    return pyautogui.position()


def move_mouse(x: int, y: int, duration: float = 0.5) -> None:
    pyautogui.moveTo(x, y, duration=duration)


def click_mouse(
    x: int | None = None,
    y: int | None = None,
    button: str = "left",
    clicks: int = 1,
    interval: float = 0.12,
) -> None:
    pyautogui.click(
        x=x,
        y=y,
        button=button,
        clicks=clicks,
        interval=interval,
    )


def drag_mouse(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: float = 0.8,
    button: str = "left",
) -> None:
    pyautogui.moveTo(start_x, start_y, duration=0.2)
    pyautogui.dragTo(end_x, end_y, duration=duration, button=button)


def scroll_mouse(amount: int, x: int | None = None, y: int | None = None) -> None:
    if x is not None and y is not None:
        pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.scroll(amount)
