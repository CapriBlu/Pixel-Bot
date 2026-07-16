import json

from pixel_bot.config.settings import PixelBotSettings
from pixel_bot.core.logger import configure_logging, get_logger, log_event


def test_structured_logging_writes_json(tmp_path):
    settings = PixelBotSettings(
        project_root=tmp_path,
        screenshots_dir=tmp_path / "screenshots",
        logs_dir=tmp_path / "logs",
        workspace_dir=tmp_path / "workspace",
        structured_logging=True,
    )
    path = configure_logging(settings, force=True)
    logger = get_logger("pixel_bot.test")

    log_event(logger, "test_event", value=7)
    for handler in logger.handlers or logger.parent.handlers:
        handler.flush()

    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["event"] == "test_event"
    assert payload["context"]["value"] == 7
