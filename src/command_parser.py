import re

from safety import Action


def parse_single_command(command: str) -> list[Action]:
    original = command.strip()
    text = original.lower()

    if not text:
        return []

    if text in {"fai uno screenshot", "screenshot", "cattura schermo"}:
        return [
            Action(
                name="screenshot",
                parameters={},
            )
        ]

    focus_match = re.fullmatch(
        r"(?:attiva|seleziona|porta in primo piano)\s+"
        r"(?:la\s+)?finestra\s+(.+)",
        original,
        flags=re.IGNORECASE,
    )

    if focus_match:
        return [
            Action(
                name="focus_window",
                parameters={
                    "title": focus_match.group(1).strip(),
                    "timeout": 5.0,
                },
            )
        ]

    open_match = re.fullmatch(
        r"(?:apri|avvia)\s+(.+)",
        text,
    )

    if open_match:
        return [
            Action(
                name="open_app",
                parameters={
                    "app": open_match.group(1).strip(),
                },
            )
        ]

    wait_match = re.fullmatch(
        r"(?:aspetta|attendi)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:secondi|secondo)?",
        text,
    )

    if wait_match:
        return [
            Action(
                name="wait",
                parameters={
                    "seconds": float(wait_match.group(1)),
                },
            )
        ]

    move_match = re.fullmatch(
        r"(?:sposta|muovi)\s+"
        r"(?:il\s+)?mouse\s+"
        r"(?:a|su)\s+"
        r"(\d+)\s*[,\s]\s*(\d+)",
        text,
    )

    if move_match:
        return [
            Action(
                name="move_mouse",
                parameters={
                    "x": int(move_match.group(1)),
                    "y": int(move_match.group(2)),
                    "duration": 0.5,
                },
            )
        ]

    click_match = re.fullmatch(
        r"(?:clicca|fai clic)\s+"
        r"(?:a|su)\s+"
        r"(\d+)\s*[,\s]\s*(\d+)",
        text,
    )

    if click_match:
        return [
            Action(
                name="click",
                parameters={
                    "x": int(click_match.group(1)),
                    "y": int(click_match.group(2)),
                },
            )
        ]

    write_match = re.fullmatch(
        r"(?:scrivi|digita)\s+(.+)",
        original,
        flags=re.IGNORECASE,
    )

    if write_match:
        return [
            Action(
                name="write_text",
                parameters={
                    "text": write_match.group(1).strip(),
                    "interval": 0.03,
                },
            )
        ]

    key_match = re.fullmatch(
        r"(?:premi)\s+(.+)",
        text,
    )

    if key_match:
        return [
            Action(
                name="press_key",
                parameters={
                    "key": key_match.group(1).strip(),
                },
            )
        ]

    raise ValueError(f"Comando non riconosciuto: {original}")


def parse_command(command: str) -> list[Action]:
    parts = [
        part.strip()
        for part in command.split(";")
        if part.strip()
    ]

    if not parts:
        raise ValueError("Il comando non può essere vuoto.")

    actions = []

    for part in parts:
        actions.extend(parse_single_command(part))

    return actions
