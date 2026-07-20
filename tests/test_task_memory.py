from pixel_bot.developer.task_memory import PersistentTaskMemory, TaskRecord


def test_roundtrip_and_event(tmp_path):
    memory = PersistentTaskMemory(tmp_path / "task.json")
    record = TaskRecord(task_id="t1", goal="test")
    memory.append_event(record, "started", round=1)
    loaded = memory.load()
    assert loaded is not None
    assert loaded.task_id == "t1"
    assert loaded.history[0]["event"] == "started"


def test_clear(tmp_path):
    memory = PersistentTaskMemory(tmp_path / "task.json")
    memory.save(TaskRecord(task_id="t1", goal="test"))
    memory.clear()
    assert memory.load() is None
