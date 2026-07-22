from __future__ import annotations

import sys
from pathlib import Path

from pixel_bot.developer.testing import TestRunner

# Pytest can attempt to collect any class in a test module whose name
# starts with "Test". The TestRunner class is a runtime helper (it has a
# non-default __init__) and is not a test case; mark it explicitly so
# pytest won't try to collect it and emit a PytestCollectionWarning.
TestRunner.__test__ = False


def test_test_runner_uses_current_python_interpreter(tmp_path: Path) -> None:
    runner = TestRunner(tmp_path)

    result = runner.run([
        "python",
        "-c",
        "import sys; print(sys.executable)",
    ])

    assert result.passed
    assert Path(result.stdout.strip()).resolve() == Path(sys.executable).resolve()
    assert Path(result.command[0]).resolve() == Path(sys.executable).resolve()


def test_test_runner_keeps_non_python_allowed_command(tmp_path: Path, monkeypatch) -> None:
    captured = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, **kwargs):
        captured["command"] = command
        return Completed()

    monkeypatch.setattr("pixel_bot.developer.testing.subprocess.run", fake_run)

    result = TestRunner(tmp_path).run(["pytest", "-q"])

    assert result.passed
    assert captured["command"] == ["pytest", "-q"]
