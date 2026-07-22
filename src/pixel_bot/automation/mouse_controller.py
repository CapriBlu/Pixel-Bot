import time
from numbers import Real

import pyautogui


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


# Limits used for validation
_MAX_DURATION = 10.0


def _validate_number(value, name: str = "value") -> None:
    if not isinstance(value, Real):
        raise ValueError(f"{name} deve essere un numero (int/float), ottenuto: {type(value)}")


def _validate_duration(duration: Real) -> None:
    _validate_number(duration, "duration")
    if duration < 0 or duration > _MAX_DURATION:
        raise ValueError(f"duration non valida: deve essere tra 0 e {_MAX_DURATION}, ottenuto: {duration}")


def _validate_coordinates(x, y) -> None:
    _validate_number(x, "x")
    _validate_number(y, "y")


def get_mouse_position():
    """Restituisce la posizione corrente del mouse.

    API invariata: ritorna direttamente pyautogui.position().
    """
    return pyautogui.position()


def move_mouse(x, y, duration=0.5):
    """Sposta il mouse alle coordinate (x, y) in modo sicuro con validazione.

    Signature e comportamento compatibili con la versione precedente.
    """
    _validate_coordinates(x, y)
    _validate_duration(duration)

    pyautogui.moveTo(x, y, duration=duration)


def click_mouse(x, y):
    """Clic sinistro sul punto (x, y).

    Mantiene la compatibilità con l'API esistente.
    """
    _validate_coordinates(x, y)

    pyautogui.click(x, y)


# Nuove operazioni sicure e validate

def right_click(x, y):
    """Clic destro sulle coordinate specificate.

    Valida input prima di delegare a PyAutoGUI.
    """
    _validate_coordinates(x, y)

    # pyautogui.rightClick esiste ma usare click con button esplicito è più portabile
    pyautogui.click(x, y, button="right")


def double_click(x, y):
    """Doppio clic sulle coordinate specificate.

    Valida input prima di delegare a PyAutoGUI.
    """
    _validate_coordinates(x, y)

    # pyautogui.doubleClick accetta x,y
    pyautogui.doubleClick(x, y)


def scroll(amount: int, x: Real | None = None, y: Real | None = None):
    """Esegue uno scroll verticale.

    amount: numero intero di 'clicks' di scroll (positivo verso l'alto, negativo verso il basso).
    x, y: opzionali coordinate dove eseguire lo scroll (validate se fornite).
    """
    if not isinstance(amount, int):
        raise ValueError(f"amount deve essere un int, ottenuto: {type(amount)}")

    if x is not None or y is not None:
        if x is None or y is None:
            raise ValueError("Se si specifica x o y, entrambe le coordinate devono essere fornite")
        _validate_coordinates(x, y)
        pyautogui.scroll(amount, x=x, y=y)
    else:
        pyautogui.scroll(amount)


def drag_mouse(start_x, start_y, end_x, end_y, duration: Real = 0.5):
    """Trascina il mouse da (start_x, start_y) a (end_x, end_y).

    Tutti i parametri sono validati prima di chiamare PyAutoGUI.
    """
    _validate_coordinates(start_x, start_y)
    _validate_coordinates(end_x, end_y)
    _validate_duration(duration)

    # Spostare al punto di partenza in modo sicuro, poi trascinare
    pyautogui.moveTo(start_x, start_y)
    pyautogui.dragTo(end_x, end_y, duration=duration)
