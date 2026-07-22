from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_exposes_controlled_auto_evolution_button() -> None:
    source = (ROOT / "launcher" / "PixelBotApp.cs").read_text(encoding="utf-8")
    assert "LANCIA AUTO-EVOLUZIONE" in source
    assert "evolutionPulseTimer" in source
    assert "RunAutoEvolutionAsync" in source
    assert "RUN_AUTO_EVOLUTION.ps1" in source
    assert "Continuare?" in source


def test_auto_evolution_is_limited_and_does_not_push() -> None:
    script = (ROOT / "launcher" / "RUN_AUTO_EVOLUTION.ps1").read_text(encoding="utf-8")
    assert "--max-tasks 1" in script
    assert "--max-attempts 1" in script
    assert "--apply" in script
    assert "--commit" in script
    assert "--push" not in script
    assert "git status --porcelain" in script
