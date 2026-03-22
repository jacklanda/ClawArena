from __future__ import annotations

import abc

from clawarena.core.result import RunResult


class StorageBackend(abc.ABC):
    @abc.abstractmethod
    async def save_run(self, result: RunResult) -> str:
        """Save a run result, return the storage path/key."""
        ...

    @abc.abstractmethod
    async def load_run(self, run_id: str) -> RunResult | None:
        ...

    @abc.abstractmethod
    async def list_runs(
        self, agent_name: str | None = None, limit: int = 50
    ) -> list[dict[str, str]]:
        """Return list of run summaries (run_id, agent, date, score)."""
        ...

    @abc.abstractmethod
    async def load_all_runs(self) -> list[RunResult]:
        ...
