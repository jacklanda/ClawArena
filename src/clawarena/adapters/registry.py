from __future__ import annotations

import importlib.metadata
from typing import Any

from clawarena.core.agent import AgentAdapter

ENTRY_POINT_GROUP = "clawarena.adapters"


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, type[AgentAdapter]] = {}
        self._discover_builtins()

    def _discover_builtins(self) -> None:
        from clawarena.adapters.builtin.dummy import DummyAdapter
        from clawarena.adapters.builtin.subprocess_adapter import SubprocessAdapter
        from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter

        self._adapters["dummy"] = DummyAdapter
        self._adapters["subprocess"] = SubprocessAdapter
        self._adapters["openclaw"] = OpenClawAdapter

    def discover_plugins(self) -> None:
        for ep in importlib.metadata.entry_points(group=ENTRY_POINT_GROUP):
            if ep.name not in self._adapters:
                self._adapters[ep.name] = ep.load()

    def get(self, name: str, **kwargs: Any) -> AgentAdapter:
        if name not in self._adapters:
            available = ", ".join(sorted(self._adapters))
            raise KeyError(f"Unknown adapter {name!r}. Available: {available}")
        return self._adapters[name](**kwargs)

    def list_available(self) -> list[str]:
        return sorted(self._adapters.keys())
