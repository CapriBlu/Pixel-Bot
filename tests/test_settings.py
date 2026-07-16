from pathlib import Path

import pytest

from pixel_bot.config.settings import PixelBotSettings


def test_settings_build_runtime_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("PIXELBOT_DEFAULT_MONITOR", "2")
    monkeypatch.setenv("PIXELBOT_STRUCTURED_LOGGING", "true")

    settings = PixelBotSettings.from_env(tmp_path)

    assert settings.project_root == tmp_path.resolve()
    assert settings.screenshots_dir == tmp_path.resolve() / "screenshots"
    assert settings.default_monitor == 2
    assert settings.structured_logging is True


def test_settings_reject_invalid_monitor(monkeypatch, tmp_path):
    monkeypatch.setenv("PIXELBOT_DEFAULT_MONITOR", "zero")

    with pytest.raises(ValueError, match="intero"):
        PixelBotSettings.from_env(tmp_path)
