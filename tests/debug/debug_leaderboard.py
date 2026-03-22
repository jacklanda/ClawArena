#!/usr/bin/env python3
"""Debug LeaderboardEntry structure."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from clawarena.core.scoring import LeaderboardEntry

print("LeaderboardEntry attributes:")
for attr in dir(LeaderboardEntry):
    if not attr.startswith("_"):
        print(f"  {attr}")

# Try to create one
import asyncio
from clawarena.adapters.registry import AdapterRegistry
from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec, TaskSuite
from clawarena.engine.runner import RunEngine
from clawarena.evaluators import get_evaluator_registry

async def test():
    task = Task(
        id="test",
        name="Test",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Test",
        instruction="Test",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=30,
    )
    
    registry = AdapterRegistry()
    adapter = registry.get("dummy")
    
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    suite = TaskSuite(name="Test", description="Test", tasks=[task])
    results = await engine.run(suite, [adapter])
    
    leaderboard = Leaderboard.from_runs(results)
    
    if leaderboard.entries:
        entry = leaderboard.entries[0]
        print("\nActual LeaderboardEntry:")
        for key, value in entry.__dict__.items():
            print(f"  {key}: {value}")

from clawarena.core.scoring import Leaderboard
asyncio.run(test())