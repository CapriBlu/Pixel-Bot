from pathlib import Path

from pixel_bot.agent.ai_client import AIClientConfig
from pixel_bot.developer.cli import main


def test_pyproject_declares_developer_console_script():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'pixelbot-developer = "pixel_bot.developer.cli:main"' in text
    assert 'package-dir = {"" = "src"}' in text


def test_cli_loads_dotenv_before_ai_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("PIXEL_BOT_DRY_RUN=1\n", encoding="utf-8")
    (tmp_path / "tasks").mkdir()

    exit_code = main(
        [
            "--next-task",
            "--repo",
            str(tmp_path),
            "--ai",
        ]
    )

    assert exit_code == 0
    assert AIClientConfig.from_environment().dry_run is True
