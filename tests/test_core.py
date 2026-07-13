import pytest

from pixel_bot.core.command_parser import parse_command
from pixel_bot.core.safety import Action, validate_action


def test_parse_screenshot():
    actions = parse_command("screenshot")

    assert len(actions) == 1
    assert actions[0].name == "screenshot"
    assert actions[0].parameters == {}


def test_parse_multiple_commands():
    actions = parse_command(
        "apri blocco note; aspetta 2 secondi; scrivi Ciao"
    )

    assert [action.name for action in actions] == [
        "open_app",
        "wait",
        "write_text",
    ]


def test_reject_unknown_action():
    action = Action(
        name="delete_everything",
        parameters={},
    )

    with pytest.raises(ValueError):
        validate_action(action)


def test_validate_safe_wait():
    action = Action(
        name="wait",
        parameters={"seconds": 2},
    )

    validate_action(action)
