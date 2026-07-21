from __future__ import annotations

import json
from pathlib import Path

from pixel_bot.developer.config_manager import ConfigManager, FoundationConfig
from pixel_bot.developer.developer_dashboard import DeveloperDashboard
from pixel_bot.developer.event_bus import EventBus
from pixel_bot.developer.foundation_runtime import FoundationRuntime
from pixel_bot.developer.health_monitor import HealthMonitor
from pixel_bot.developer.plugin_registry import Plugin, PluginRegistry
from pixel_bot.developer.self_analysis import SelfAnalysisEngine


def test_event_bus_journal_and_subscriber(tmp_path: Path) -> None:
    journal = tmp_path / "events.jsonl"
    bus = EventBus(journal)
    seen = []
    bus.subscribe("task_started", seen.append)
    event = bus.publish("task_started", {"task_id": "T1"})
    assert event.sequence == 1
    assert seen[0].payload["task_id"] == "T1"
    assert EventBus.read_journal(journal)[0]["type"] == "task_started"


def test_event_bus_wildcard_and_unsubscribe() -> None:
    bus = EventBus()
    seen = []
    stop = bus.subscribe("*", seen.append)
    bus.publish("one")
    stop()
    bus.publish("two")
    assert [event.type for event in seen] == ["one"]


def test_config_roundtrip(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "config.json")
    cfg = manager.load()
    cfg.max_rounds = 33
    manager.save(cfg)
    assert manager.load().max_rounds == 33


def test_config_validation() -> None:
    cfg = FoundationConfig(max_attempts=0)
    try:
        cfg.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("validation expected")


def test_plugin_registry() -> None:
    registry = PluginRegistry()
    registry.register(Plugin("demo", "1.0", lambda value=1: value + 1))
    assert registry.create("demo", value=4) == 5
    assert registry.describe() == [{"name": "demo", "version": "1.0"}]


def test_health_monitor() -> None:
    monitor = HealthMonitor()
    healthy = monitor.sample()
    degraded = monitor.sample(watchdog_tripped=True)
    assert healthy.status == "healthy"
    assert degraded.status == "degraded"
    assert healthy.pid > 0


def test_self_analysis() -> None:
    events = [
        {"type": "step_retry_scheduled", "payload": {"error_type": "verification_failed"}},
        {"type": "step_retry_scheduled", "payload": {"error_type": "watchdog_timeout"}},
    ]
    report = SelfAnalysisEngine().analyze(events)
    assert report.retries == 2
    assert report.failures == 2
    assert report.watchdog_interventions == 1
    assert report.recommendations


def test_dashboard_render(tmp_path: Path) -> None:
    target = DeveloperDashboard().render(
        tmp_path / "dashboard.html",
        [{"sequence": 1, "timestamp": "now", "type": "test", "payload": {"x": "<ok>"}}],
        {"status": "healthy"},
        {"failures": 0},
    )
    text = target.read_text(encoding="utf-8")
    assert "Pixel-Bot Foundation Dashboard" in text
    assert "&lt;ok&gt;" in text


def test_foundation_runtime(tmp_path: Path) -> None:
    runtime = FoundationRuntime(tmp_path)
    runtime.event_bus.publish("task_started", {"task_id": "T1"})
    output = runtime.build_dashboard(provider="test")
    assert output.exists()
    assert (tmp_path / "foundation_config.json").exists()
    assert json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()[0])["type"] == "task_started"
