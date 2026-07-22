import json

import pytest

from pixel_bot.agent.memory import AgentMemory
from pixel_bot.agent.workspace import WORKSPACE_SECTIONS, Workspace


def test_workspace_initializes_all_sections(tmp_path):
    workspace = Workspace(root=tmp_path / "workspace")
    workspace.initialize()

    assert workspace.session_dir.exists()
    for section in WORKSPACE_SECTIONS:
        assert (workspace.root / section).is_dir()


def test_workspace_session_ids_are_unique(tmp_path):
    first = Workspace(root=tmp_path / "workspace")
    second = Workspace(root=tmp_path / "workspace")

    assert first.session_id != second.session_id


def test_workspace_appends_and_reads_recent_events(tmp_path):
    workspace = Workspace(root=tmp_path / "workspace")
    for index in range(5):
        workspace.append_event("event", {"index": index})

    recent = workspace.recent_events(limit=2)

    assert [item["payload"]["index"] for item in recent] == [3, 4]


def test_workspace_saves_summary(tmp_path):
    workspace = Workspace(root=tmp_path / "workspace")
    path = workspace.save_summary({"status": "completed"})
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["session_id"] == workspace.session_id
    assert payload["status"] == "completed"


def test_workspace_rejects_path_traversal(tmp_path):
    workspace = Workspace(root=tmp_path / "workspace")

    with pytest.raises(ValueError):
        workspace.safe_path("history", "../escape.json")


def test_memory_persists_and_limits_recent_entries(tmp_path):
    path = tmp_path / "memory.json"
    memory = AgentMemory(path)

    for index in range(4):
        memory.append({"index": index})

    restored = AgentMemory(path)
    restored.load()

    assert restored.recent(limit=2) == [{"index": 2}, {"index": 3}]
