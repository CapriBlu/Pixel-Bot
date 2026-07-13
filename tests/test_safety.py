import pytest

from pixel_bot.core.safety import Action, validate_action


def test_reject_negative_coordinates():
    action = Action(
        name="click",
        parameters={
            "x": -1,
            "y": 100,
        },
    )

    with pytest.raises(ValueError):
        validate_action(action)


def test_reject_excessive_wait():
    action = Action(
        name="wait",
        parameters={
            "seconds": 60,
        },
    )

    with pytest.raises(ValueError):
        validate_action(action)


def test_reject_unknown_application():
    action = Action(
        name="open_app",
        parameters={
            "app": "programma sconosciuto",
        },
    )

    with pytest.raises(ValueError):
        validate_action(action)


def test_reject_empty_window_title():
    action = Action(
        name="focus_window",
        parameters={
            "title": "",
        },
    )

    with pytest.raises(ValueError):
        validate_action(action)
