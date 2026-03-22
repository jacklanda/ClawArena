#!/usr/bin/env python3
"""Debug how to get all tasks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from clawarena.tasks.registry import TaskRegistry

registry = TaskRegistry()

print("TaskRegistry methods:")
for attr in dir(registry):
    if not attr.startswith("_"):
        print(f"  {attr}")

# Try to get tasks
print("\nTrying to get tasks...")

# Method 1: Check if there's a method to get all
try:
    # Try to call the registry
    tasks = registry._tasks  # Check internal attribute
    print(f"Found {len(tasks)} tasks in _tasks")
except:
    print("No _tasks attribute")

# Method 2: Try to create a suite
from clawarena.core.task import TaskSuite
try:
    suite = registry.as_suite("All Tasks")
    print(f"Suite created with {len(suite)} tasks")
    for task in suite.tasks[:3]:  # Show first 3
        print(f"  - {task.name} ({task.category.value})")
except Exception as e:
    print(f"Suite creation failed: {e}")