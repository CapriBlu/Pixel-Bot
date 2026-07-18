from __future__ import annotations

from pathlib import Path

import pytest

from pixel_bot.developer.failure_registry import FailureRegistry


def test_failure_registry_instantiation(tmp_path: Path) -> None:
    # Should not raise AttributeError when creating the registry
    reg = FailureRegistry(repository_root=tmp_path)
    assert isinstance(reg, FailureRegistry)


def test_failure_registry_path_computed_correctly(tmp_path: Path) -> None:
    reg = FailureRegistry(repository_root=tmp_path)
    expected = (tmp_path / "workspace" / "test-failure-registry").resolve()
    assert reg.path == expected


def test_record_and_list(tmp_path: Path) -> None:
    reg = FailureRegistry(repository_root=tmp_path)
    # record a file and check it appears in the listing
    written = reg.record("failure1.txt", "payload")
    assert written.exists()
    entries = reg.list_entries()
    assert any(p.name == "failure1.txt" for p in entries)

    # clearing should remove the file
    reg.clear()
    entries_after = reg.list_entries()
    assert all(p.name != "failure1.txt" for p in entries_after)
