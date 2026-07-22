from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_start_button_uses_current_repository_runner() -> None:
    source = (ROOT / "launcher" / "PixelBotApp.cs").read_text(encoding="utf-8")
    assert 'runner = Path.Combine(launcherDir, "RUN_PIXEL_BOT.ps1")' in source
    assert 'runner = Path.Combine(launcherDir, "RUN_AUTO_005_2.ps1")' not in source
    assert "OneDrive" not in source


def test_current_runner_has_no_legacy_onedrive_or_auto_task() -> None:
    script = (ROOT / "launcher" / "RUN_PIXEL_BOT.ps1").read_text(encoding="utf-8")
    assert "C:\\Dev\\Pixel-Bot" in script
    assert "OneDrive" not in script
    assert "AUTO-005" not in script
    assert "$env:PYTHONPATH" in script
    assert "from pixel_bot.developer import cli" in script
    assert "callable(cli.main)" in script
