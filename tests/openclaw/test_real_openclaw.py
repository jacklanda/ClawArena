#!/usr/bin/env python3
"""
Real test of OpenClaw adapter with actual OpenClaw installation.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_openclaw_with_real_claude():
    """Test OpenClaw adapter with real Claude agent."""
    print("🧪 Testing OpenClaw Adapter with Real Claude")
    print("=" * 60)
    
    from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create a simple task
    task = Task(
        id="simple_greeting",
        name="Simple Greeting",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="A simple greeting task",
        instruction="Say 'Hello, world!' in a creative way.",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=30,
    )
    
    # Create OpenClaw adapter
    adapter = OpenClawAdapter(
        agent_id="claude",
        timeout_seconds=30,
    )
    
    print(f"Task: {task.name}")
    print(f"Instruction: {task.instruction}")
    print(f"Adapter: {adapter.info().name}")
    print("\n🚀 Executing task...")
    
    try:
        # Execute the task
        response = await adapter.run_task(task)
        
        print(f"\n✅ Execution completed!")
        print(f"Duration: {response.duration_seconds:.2f}s")
        print(f"Tokens: {response.token_usage.total_tokens}")
        print(f"Error: {response.error if response.error else 'None'}")
        
        print(f"\n📝 Response:")
        print("-" * 40)
        print(response.output)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_openclaw_with_dummy():
    """Test with dummy adapter for comparison."""
    print("\n🧪 Testing Dummy Adapter for Comparison")
    print("=" * 60)
    
    from clawarena.adapters.builtin.dummy import DummyAdapter
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create the same task
    task = Task(
        id="simple_greeting",
        name="Simple Greeting",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="A simple greeting task",
        instruction="Say 'Hello, world!' in a creative way.",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=30,
    )
    
    adapter = DummyAdapter()
    
    print(f"Task: {task.name}")
    print(f"Adapter: {adapter.info().name}")
    print("\n🚀 Executing task...")
    
    try:
        response = await adapter.run_task(task)
        
        print(f"\n✅ Dummy execution completed!")
        print(f"Duration: {response.duration_seconds:.2f}s")
        print(f"Tokens: {response.token_usage.total_tokens}")
        
        print(f"\n📝 Dummy Response:")
        print("-" * 40)
        print(response.output[:200] + "..." if len(response.output) > 200 else response.output)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Dummy execution failed: {e}")
        return False

async def test_cli_style_execution():
    """Test execution in CLI style."""
    print("\n🧪 Testing CLI-style Execution")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Get adapter from registry (like CLI would)
    registry = AdapterRegistry()
    
    print("Available adapters:", registry.list_available())
    
    try:
        # Try to get OpenClaw adapter
        adapter = registry.get("openclaw", agent_id="claude")
        print(f"✅ Got adapter: {adapter.info().name}")
        
        # Create a task
        task = Task(
            id="cli_test",
            name="CLI Test Task",
            category=TaskCategory("general"),
            difficulty=TaskDifficulty("easy"),
            description="CLI style test",
            instruction="What is 2 + 2?",
            evaluation=EvaluationSpec(evaluator="exact_match", config={}),
            timeout_seconds=30,
        )
        
        print(f"\nTask: {task.name}")
        print(f"Question: {task.instruction}")
        
        # Execute
        response = await adapter.run_task(task)
        
        print(f"\n✅ CLI-style execution worked!")
        print(f"Answer: {response.output[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI-style test failed: {e}")
        return False

async def main():
    """Run all real tests."""
    print("🚀 Real OpenClaw Integration Test")
    print("=" * 60)
    
    print("Checking OpenClaw installation...")
    import subprocess
    try:
        result = subprocess.run(["openclaw", "--version"], 
                              capture_output=True, text=True)
        print(f"✅ OpenClaw found: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ OpenClaw check failed: {e}")
        return False
    
    results = []
    
    # Test 1: Dummy adapter (should always work)
    try:
        dummy_ok = await test_openclaw_with_dummy()
        results.append(("Dummy Adapter", dummy_ok))
    except Exception as e:
        print(f"❌ Dummy test crashed: {e}")
        results.append(("Dummy Adapter", False))
    
    # Test 2: CLI-style execution
    try:
        cli_ok = await test_cli_style_execution()
        results.append(("CLI-style", cli_ok))
    except Exception as e:
        print(f"❌ CLI test crashed: {e}")
        results.append(("CLI-style", False))
    
    # Test 3: Real OpenClaw with Claude
    print("\n⚠ Note: Real OpenClaw test may take time and use API credits")
    print("   Skipping real test by default (run manually if needed)")
    
    # Skip by default to avoid API costs
    print("Skipping real OpenClaw test (run manually with caution)")
    results.append(("Real OpenClaw", "skipped"))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, success in results:
        if success == "skipped":
            status = "⏭ SKIPPED"
        elif success:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, success in results if success is True)
    total = sum(1 for _, success in results if success is not False)
    
    print(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! OpenClaw integration is working!")
    else:
        print(f"\n⚠ {total - passed} tests failed or were skipped.")
    
    print("\n" + "=" * 60)
    print("🚀 Next Steps:")
    print("1. Run full benchmark: clawarena run --agent openclaw:agent_id=claude")
    print("2. Test different agents: clawarena run --agent openclaw:agent_id=gpt-4")
    print("3. Compare agents: clawarena run --agent openclaw:agent_id=claude --agent dummy")
    print("4. View results: clawarena leaderboard")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)