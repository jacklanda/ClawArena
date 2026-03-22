#!/usr/bin/env python3
"""Debug the RunResult structure."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def debug():
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec, TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    
    # Create task
    task = Task(
        id="debug_test",
        name="Debug Test",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Debug",
        instruction="Test",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=30,
    )
    
    # Get adapter
    registry = AdapterRegistry()
    adapter = registry.get("dummy")
    
    # Run
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    suite = TaskSuite(name="Debug", description="Debug", tasks=[task])
    results = await engine.run(suite, [adapter])
    
    print("Results type:", type(results))
    print("Results length:", len(results))
    
    if results:
        result = results[0]
        print("\nResult attributes:")
        for attr in dir(result):
            if not attr.startswith("_"):
                print(f"  {attr}")
        
        print("\nResult details:")
        print(f"  Type: {type(result)}")
        if hasattr(result, '__dict__'):
            for key, value in result.__dict__.items():
                print(f"  {key}: {type(value)} = {value}")

asyncio.run(debug())