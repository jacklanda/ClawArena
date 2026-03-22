"""
Optimized adapter registry with improved OpenClaw adapter.
"""

from __future__ import annotations

import importlib.metadata
from typing import Any

from clawarena.core.agent import AgentAdapter

ENTRY_POINT_GROUP = "clawarena.adapters"


class OptimizedAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, type[AgentAdapter]] = {}
        self._discover_builtins()

    def _discover_builtins(self) -> None:
        from clawarena.adapters.builtin.dummy import DummyAdapter
        from clawarena.adapters.builtin.subprocess_adapter import SubprocessAdapter
        from clawarena.adapters.builtin.openclaw_adapter_optimized import (
            OptimizedOpenClawAdapter,
            openclaw_factory,
        )

        self._adapters["dummy"] = DummyAdapter
        self._adapters["subprocess"] = SubprocessAdapter
        
        # Register optimized OpenClaw adapter with factory function
        # Note: We use a factory function because OptimizedOpenClawAdapter
        # needs to be instantiated with parameters
        self._adapters["openclaw"] = openclaw_factory
        self._adapters["openclaw-optimized"] = openclaw_factory

    def discover_plugins(self) -> None:
        for ep in importlib.metadata.entry_points(group=ENTRY_POINT_GROUP):
            if ep.name not in self._adapters:
                self._adapters[ep.name] = ep.load()

    def get(self, name: str, **kwargs: Any) -> AgentAdapter:
        if name not in self._adapters:
            available = ", ".join(sorted(self._adapters))
            raise KeyError(f"Unknown adapter {name!r}. Available: {available}")
        
        # Special handling for OpenClaw adapter
        if name in ["openclaw", "openclaw-optimized"]:
            # Ensure agent_id is provided
            if "agent_id" not in kwargs:
                kwargs["agent_id"] = "main"
            
            # Add debug mode if requested
            if "enable_debug" not in kwargs:
                kwargs["enable_debug"] = False
        
        return self._adapters[name](**kwargs)

    def list_available(self) -> list[str]:
        return sorted(self._adapters.keys())
    
    def get_adapter_info(self, name: str) -> dict:
        """Get information about a specific adapter."""
        if name not in self._adapters:
            raise KeyError(f"Unknown adapter {name}")
        
        # Create a minimal instance to get info
        try:
            if name in ["openclaw", "openclaw-optimized"]:
                adapter = self._adapters[name](agent_id="test")
            else:
                adapter = self._adapters[name]()
            
            info = adapter.info()
            return {
                "name": info.name,
                "version": info.version,
                "model": info.model,
                "description": info.description,
                "metadata": info.metadata,
            }
        except Exception as e:
            return {
                "name": name,
                "error": str(e),
            }


# Global registry instance
optimized_registry = OptimizedAdapterRegistry()