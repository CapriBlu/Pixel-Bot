import time

import pygetwindow as gw


def find_window(title: str):
    normalized_title = title.strip().lower()

    matches = [
        window
        for window in gw.getAllWindows()
        if normalized_title in window.title.lower()
    ]

    if not matches:
        raise RuntimeError(f"Finestra non trovata: {title}")

    return matches[0]


def focus_window(title: str, timeout: float = 5.0):
    deadline = time.time() + timeout
    last_error = None

    while time.time() < deadline:
        try:
            window = find_window(title)

            if window.isMinimized:
                window.restore()
                time.sleep(0.3)

            window.activate()
            time.sleep(0.5)

            active = gw.getActiveWindow()

            if active and title.lower() in active.title.lower():
                return active

        except Exception as error:
            last_error = error

        time.sleep(0.3)

    raise RuntimeError(
        f"Impossibile attivare la finestra '{title}': {last_error}"
    )


def get_active_window_title() -> str:
    active = gw.getActiveWindow()

    if active is None:
        return ""

    return active.title
