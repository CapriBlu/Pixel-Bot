from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class Plugin:
    name: str
    version: str
    factory: Callable[..., Any]


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        if not plugin.name.strip():
            raise ValueError("Il nome del plugin non può essere vuoto")
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin già registrato: {plugin.name}")
        self._plugins[plugin.name] = plugin

    def create(self, name: str, **kwargs: Any) -> Any:
        try:
            return self._plugins[name].factory(**kwargs)
        except KeyError as exc:
            raise KeyError(f"Plugin non registrato: {name}") from exc

    def describe(self) -> list[dict[str, str]]:
        return [{"name": p.name, "version": p.version} for p in sorted(self._plugins.values(), key=lambda p: p.name)]
