from pathlib import Path

from pixel_bot.developer.repository_intelligence import RepositoryIntelligence


def test_classifies_source_as_stage(tmp_path: Path) -> None:
    intelligence = RepositoryIntelligence(tmp_path)
    decision = intelligence._classify_local("??", "src/pixel_bot/example.py")
    assert decision.action == "stage"
    assert decision.confidence >= 0.9


def test_protects_env(tmp_path: Path) -> None:
    intelligence = RepositoryIntelligence(tmp_path)
    decision = intelligence._classify_local("??", ".env")
    assert decision.action == "ignore"
    assert decision.category == "secret"


def test_image_requires_inspection(tmp_path: Path) -> None:
    intelligence = RepositoryIntelligence(tmp_path)
    decision = intelligence._classify_local("??", "random-photo.png")
    assert decision.action == "inspect"
