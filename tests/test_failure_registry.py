from pathlib import Path

from pixel_bot.developer.failure_registry import FailureRegistry


def test_failure_registry_initialization_and_record(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    # instantiate (should not raise AttributeError)
    registry = FailureRegistry(workspace)

    expected = workspace / "test-failure-registry"
    assert registry.registry_path == expected
    # directory must be created by initialization
    assert expected.exists() and expected.is_dir()

    # record a payload and check file existence and content
    payload = {"error": "simulated", "code": 123}
    file_path = registry.record("sample_failure", payload)
    assert file_path.exists() and file_path.is_file()
    loaded = file_path.read_text(encoding="utf-8")
    assert "simulated" in loaded
