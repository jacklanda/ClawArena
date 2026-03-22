from __future__ import annotations

from clawarena.core.result import RunResult
from clawarena.core.scoring import Leaderboard
from clawarena.storage.backend import StorageBackend


async def compute_leaderboard(storage: StorageBackend) -> Leaderboard:
    runs = await storage.load_all_runs()
    return Leaderboard.from_runs(runs)
