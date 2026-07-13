from unittest.mock import patch

from pixel_bot.core.executor import execute_action
from pixel_bot.core.safety import Action


@patch("pixel_bot.core.executor.capture_screen")
def test_execute_screenshot(mock_capture):
    mock_capture.return_value = "screenshots/test.png"

    result = execute_action(
        Action(
            name="screenshot",
            parameters={},
        )
    )

    assert result == "screenshots/test.png"
    mock_capture.assert_called_once_with()


@patch("pixel_bot.core.executor.move_mouse")
def test_execute_move_mouse(mock_move):
    execute_action(
        Action(
            name="move_mouse",
            parameters={
                "x": 100,
                "y": 200,
                "duration": 0.5,
            },
        )
    )

    mock_move.assert_called_once_with(100, 200, 0.5)


@patch("pixel_bot.core.executor.write_text")
def test_execute_write_text(mock_write):
    execute_action(
        Action(
            name="write_text",
            parameters={
                "text": "Ciao",
                "interval": 0.03,
            },
        )
    )

    mock_write.assert_called_once_with("Ciao", 0.03)


@patch("pixel_bot.core.executor.subprocess.Popen")
def test_execute_open_app(mock_popen):
    result = execute_action(
        Action(
            name="open_app",
            parameters={
                "app": "blocco note",
            },
        )
    )

    assert result == "notepad.exe"
    mock_popen.assert_called_once_with(["notepad.exe"])


@patch("pixel_bot.core.executor.focus_window")
def test_execute_focus_window(mock_focus):
    mock_focus.return_value.title = "Blocco note"

    result = execute_action(
        Action(
            name="focus_window",
            parameters={
                "title": "Blocco note",
                "timeout": 5.0,
            },
        )
    )

    assert result == "Blocco note"
    mock_focus.assert_called_once_with("Blocco note", 5.0)
