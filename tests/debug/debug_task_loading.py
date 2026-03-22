#!/usr/bin/env python3
"""Debug task loading methods."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from clawarena.tasks.registry import TaskRegistry

registry = TaskRegistry()

print("TaskRegistry methods:")
for attr in dir(registry):
    if not attr.startswith("_"):
        print(f"  {attr}")

# Try to add directory
task_dir = Path(__file__).parent / "tasks" / "openclaw"
print(f"\nTask directory exists: {task_dir.exists()}")

if task_dir.exists():
    try:
        registry.add_directory(task_dir)
        print("✅ Directory added successfully")
        
        # List all tasks
        tasks = registry.list_all()
        print(f"\nTotal tasks loaded: {len(tasks)}")
        
        # Find our currency task
        for task in tasks:
            if "currency" in task.name.lower() or "currency" in task.id:
                print(f"\nFound currency task:")
                print(f"  ID: {task.id}")
                print(f"  Name: {task.name}")
                print(f"  Category: {task.category.value}")
                break
        else:
            print("\n❌ Currency task not found in loaded tasks")
            
    except Exception as e:
        print(f"❌ Error adding directory: {e}")