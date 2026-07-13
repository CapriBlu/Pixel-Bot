import re

from safety import Action


def parse_command(command: str) -> list[Action]:
    text = command.strip().lower()

    if not text:
        raise ValueError("Il comando non può essere vuoto.")

    if text in {"fai uno screenshot", "screenshot", "cattura schermo"}:
        return [
            Action(
                name="screenshot",
                parameters={},
            )
        ]

    wait_match = re.fullmatch(
        r"(?:aspetta|attendi)\s+(\d+(?:\.\d+)?)\s*(?:secondi|secondo)?",
        text,
    )

    if wait_match:
        seconds = float(wait_match.group(1))

        return [
            Action(
                name="wait",
                parameters={"seconds": seconds},
            )
        ]

    move_match = re.fullmatch(
        r"(?:sposta|muovi)\s+(?:il\s+)?mouse\s+(?:a|su)\s+(\d+)\s*[,\s]\s*(\d+)",
        text,
    )

    if move_match:
        x = int(move_match.group(1))
        y = int(move_match.group(2))

        return [
            Action(
                name="move_mouse",
                parameters={
                    "x": x,
                    "y": y,
                    "duration": 0.5,
                },
            )
        ]

    click_match = re.fullmatch(
        r"(?:clicca|fai clic)\s+(?:a|su)\s+(\d+)\s*[,\s]\s*(\d+)",
        text,
    )

    if click_match:
        x = int(click_match.group(1))
        y = int(click_match.group(2))

        return [
            Action(
                name="click",
                parameters={
                    "x": x,
                    "y": y,
                },
            )
        ]

    write_match = re.fullmatch(
        r"(?:scrivi|digita)\s+(.+)",
        command.strip(),
        flags=re.IGNORECASE,
    )

    if write_match:
        content = write_match.group(1).strip()

        return [
            Action(
                name="write_text",
                parameters={
                    "text": content,
                    "interval": 0.03,
                },
            )
        ]

    raise ValueError(
        "Comando non riconosciuto. "
        "Prova: screenshot, aspetta 2 secondi, "
        "muovi il mouse a 300 300, clicca su 300 300, scrivi Ciao."
    )
