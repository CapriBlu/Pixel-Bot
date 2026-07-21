from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _executable_lines(script: str) -> str:
    """Return PowerShell lines that are not comments or blank lines."""
    return "\n".join(
        line for line in script.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def test_runner_uses_import_probe_without_truncated_help_pipeline() -> None:
    script = (ROOT / "launcher" / "RUN_PIXEL_BOT.ps1").read_text(encoding="utf-8")
    executable = _executable_lines(script)

    assert "from pixel_bot.developer import cli" in executable
    assert "callable(cli.main)" in executable
    assert "--help | Select-Object" not in executable


def test_runner_targets_current_repository() -> None:
    script = (ROOT / "launcher" / "RUN_PIXEL_BOT.ps1").read_text(encoding="utf-8")
    assert "C:\\Dev\\Pixel-Bot" in script
    assert "OneDrive" not in script
