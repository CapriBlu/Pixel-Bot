from __future__ import annotations

from pathlib import Path
from typing import Any

from .config_manager import ConfigManager
from .developer_dashboard import DeveloperDashboard
from .event_bus import EventBus
from .health_monitor import HealthMonitor
from .plugin_registry import PluginRegistry
from .self_analysis import SelfAnalysisEngine


class FoundationRuntime:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.config = ConfigManager(workspace / "foundation_config.json").load()
        self.journal_path = workspace / "events.jsonl"
        self.event_bus = EventBus(self.journal_path if self.config.journal_enabled else None)
        self.health = HealthMonitor()
        self.plugins = PluginRegistry()
        self.analysis = SelfAnalysisEngine()
        self.dashboard = DeveloperDashboard()

    def build_dashboard(self, **details: Any) -> Path:
        events = EventBus.read_journal(self.journal_path, self.config.dashboard_history_limit)
        health = self.health.as_dict(self.health.sample(**details))
        analysis = self.analysis.analyze(events).as_dict()
        return self.dashboard.render(self.workspace / "dashboard.html", events, health, analysis)
