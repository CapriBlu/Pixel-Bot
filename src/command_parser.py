import re

from safety import Action


def parse_single_command(command: str) -> list[Action]:
    original = command.strip()
    text = original.lower()

    if not text:
        return []

    if text in {"fai uno screenshot", "screenshot", "cattura schermo"}:
        return [Action(name="screenshot", parameters={})]

    open_match = re.fullmatch(
        r"(?:apri|avvia)\s+(.+)",
        text,
    )

    if open_match:
        app = open_match.group(1).strip()

        return [
            Action(
                name="open_app",
                parameters={"app": app},
            )
        ]

    wait_match = re.fullmatch(
        r"(?:aspetta|attendi)\s+(\d+(?:\.\d+)?)\s*(?:secondi|secondo)?",
        text,
    )

    if wait_match:
        return [
            Action(
                name="wait",
                parameters={"seconds": float(wait_match.group(1))},
            )
        ]

    move_match = re.fullmatch(
        r"(?:sposta|muovi)\s+(?:il\s+)?mouse\s+(?:a|su)\s+(\d+)\s*[,\s]\s*(\d+)",
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
        r"(?:clicca|fai clic)\s+(?:a|su)\s+(\d+)\s*[,\s]\s*(\d+)",
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
                parameters={"key": key_match.group(1).strip()},
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
