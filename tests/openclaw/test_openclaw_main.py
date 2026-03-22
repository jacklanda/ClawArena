#!/usr/bin/env python3
"""Test OpenClaw with main agent."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_main_agent():
    """Test with main agent."""
    from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create adapter with main agent
    adapter = OpenClawAdapter(
        agent_id="main",  # Use main agent
        timeout_seconds=30,
    )
    
    print(f"Adapter: {adapter.info().name}")
    
    # Create a simple task
    task = Task(
        id="test_main",
        name="Test Main Agent",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Test main agent",
        instruction="What is the capital of France?",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=30,
    )
    
    print(f"Task: {task.name}")
    print(f"Instruction: {task.instruction}")
    
    try:
        response = await adapter.run_task(task)
        
        print(f"\n✅ Success!")
        print(f"Duration: {response.duration_seconds:.2f}s")
        print(f"Tokens: {response.token_usage.total_tokens}")
        print(f"Error: {response.error if response.error else 'None'}")
        
        print(f"\n📝 Response:")
        print("-" * 40)
        print(response.output)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🧪 Testing OpenClaw with Main Agent")
    print("=" * 60)
    
    success = await test_main_agent()
    
    if success:
        print("\n🎉 Test successful!")
    else:
        print("\n⚠ Test failed")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹ Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)