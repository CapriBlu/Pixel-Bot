from pathlib import Path

import pytest

from pixel_bot.developer.state_tools import SafeToolRegistry


def test_rejects_path_outside_repository(tmp_path: Path):
    registry = SafeToolRegistry(tmp_path)
    with pytest.raises(ValueError):
        registry.read_file("../secret.txt", 100)


def test_reads_safe_file(tmp_path: Path):
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    registry = SafeToolRegistry(tmp_path)
    assert registry.read_file("hello.txt", 100) == "hello"
