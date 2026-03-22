#!/usr/bin/env python3
"""Test task creation to understand the API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec

# Try different ways to create EvaluationSpec
try:
    # Method 1: Direct creation
    eval_spec = EvaluationSpec(evaluator="exact_match", config={})
    print(f"✅ EvaluationSpec created: {eval_spec}")
except Exception as e:
    print(f"❌ Method 1 failed: {e}")

# Try creating a full task
try:
    task = Task(
        id="test_task",
        name="Test Task",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Test description",
        instruction="Test instruction",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=60,
    )
    print(f"✅ Task created: {task.name}")
    print(f"   ID: {task.id}")
    print(f"   Category: {task.category}")
    print(f"   Evaluation: {task.evaluation}")
except Exception as e:
    print(f"❌ Task creation failed: {e}")
    import traceback
    traceback.print_exc()