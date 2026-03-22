#!/usr/bin/env python3
"""Fix OpenClaw task YAML files to match ClawArena schema."""

import yaml
from pathlib import Path

def fix_task_file(file_path):
    """Fix a task YAML file."""
    print(f"🔧 Fixing: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace evaluation structure
    if 'evaluation:\n  method: rubric' in content:
        content = content.replace('evaluation:\n  method: rubric', 'evaluation:\n  evaluator: rubric')
        print("  ✅ Fixed evaluation.evaluator")
    
    # Replace execution_mode
    if 'execution_mode: single_turn' in content:
        content = content.replace('execution_mode: single_turn', 'execution_mode: sandboxed')
        print("  ✅ Fixed execution_mode")
    elif 'execution_mode: multi_step' in content:
        content = content.replace('execution_mode: multi_step', 'execution_mode: sandboxed')
        print("  ✅ Fixed execution_mode")
    
    # Check for missing description
    lines = content.split('\n')
    has_description = any(line.strip().startswith('description:') for line in lines)
    
    if not has_description:
        # Find where to insert description
        for i, line in enumerate(lines):
            if line.strip().startswith('difficulty:'):
                # Insert description after difficulty
                desc_line = line.replace('difficulty:', 'description: "Task description"')
                lines.insert(i + 1, desc_line)
                print("  ✅ Added description field")
                break
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True

def main():
    """Fix all OpenClaw task files."""
    task_dir = Path(__file__).parent / "tasks" / "openclaw"
    
    if not task_dir.exists():
        print(f"❌ Task directory not found: {task_dir}")
        return
    
    print(f"📁 Fixing tasks in: {task_dir}")
    
    task_files = list(task_dir.glob("*.yaml"))
    print(f"Found {len(task_files)} task files")
    
    for task_file in task_files:
        try:
            fix_task_file(task_file)
        except Exception as e:
            print(f"  ❌ Error fixing {task_file.name}: {e}")
    
    print("\n✅ All task files fixed!")
    
    # Test loading
    print("\n🧪 Testing task loading...")
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from clawarena.tasks.registry import TaskRegistry
        registry = TaskRegistry()
        registry.add_directory(task_dir)
        
        tasks = registry.list_all()
        print(f"✅ Successfully loaded {len(tasks)} tasks")
        
        for task in tasks:
            if "openclaw" in task.id:
                print(f"  - {task.name} ({task.id})")
                
    except Exception as e:
        print(f"❌ Error loading tasks: {e}")

if __name__ == "__main__":
    main()