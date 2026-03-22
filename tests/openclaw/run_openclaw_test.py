#!/usr/bin/env python3
"""
Run a simple OpenClaw test through ClawArena.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def run_single_task():
    """Run a single task with OpenClaw adapter."""
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    
    print("🚀 Running OpenClaw Test")
    print("=" * 60)
    
    # Create a simple task
    task = Task(
        id="openclaw_test_001",
        name="OpenClaw Test Task",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Test OpenClaw adapter functionality",
        instruction="Write a short haiku about artificial intelligence.",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=60,
    )
    
    # Get adapter
    registry = AdapterRegistry()
    
    print("Available adapters:", registry.list_available())
    
    # Create adapters to compare
    adapters = []
    
    # Dummy adapter for baseline
    dummy_adapter = registry.get("dummy")
    adapters.append(dummy_adapter)
    print(f"\n📦 Loaded: {dummy_adapter.info().name}")
    
    # OpenClaw adapter
    try:
        openclaw_adapter = registry.get("openclaw", agent_id="main")
        adapters.append(openclaw_adapter)
        print(f"📦 Loaded: {openclaw_adapter.info().name}")
    except Exception as e:
        print(f"⚠ Could not load OpenClaw adapter: {e}")
        print("   Using dummy adapter only")
    
    # Run task
    print(f"\n🎯 Task: {task.name}")
    print(f"   Instruction: {task.instruction}")
    
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    
    # Create TaskSuite
    from clawarena.core.task import TaskSuite
    suite = TaskSuite(name="OpenClaw Test", description="Test suite", tasks=[task])
    
    print("\n🚀 Executing...")
    results = await engine.run(suite, adapters)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 Results")
    print("=" * 60)
    
    for run_result in results:
        print(f"\n🔧 Agent: {run_result.agent.name}")
        print(f"   Run ID: {run_result.run_id}")
        print(f"   Aggregate Score: {run_result.aggregate_score:.2f}/100")
        print(f"   Total Duration: {run_result.total_duration_seconds:.2f}s")
        print(f"   Total Tokens: {run_result.total_tokens.total_tokens}")
        print(f"   Total Cost: ${run_result.total_cost.total_cost_usd:.4f}")
        
        # Show task results
        for task_result in run_result.task_results:
            print(f"\n   📋 Task: {task_result.task_name}")
            print(f"      Score: {task_result.score.overall:.2f}/100")
            print(f"      Passed: {'✅' if task_result.passed else '❌'}")
            
            if task_result.error:
                print(f"      ❌ Error: {task_result.error}")
            else:
                # Show output preview
                output_preview = task_result.agent_response.output
                if len(output_preview) > 150:
                    output_preview = output_preview[:150] + "..."
                print(f"      📝 Output: {output_preview}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Summary")
    print("=" * 60)
    
    successful_runs = [r for r in results if all(tr.passed for tr in r.task_results)]
    total_tasks = sum(len(r.task_results) for r in results)
    successful_tasks = sum(sum(1 for tr in r.task_results if tr.passed) for r in results)
    
    if results:
        best = max(results, key=lambda r: r.aggregate_score)
        print(f"🏆 Best agent: {best.agent.name} ({best.aggregate_score:.2f})")
    
    print(f"Total runs: {len(results)}")
    print(f"Successful runs: {len(successful_runs)}")
    print(f"Total tasks executed: {total_tasks}")
    print(f"Successful tasks: {successful_tasks}")
    print(f"Failed tasks: {total_tasks - successful_tasks}")
    
    return len(successful_runs) > 0

def main():
    """Main entry point."""
    print("ClawArena OpenClaw Integration Test")
    print("=" * 60)
    
    # Check OpenClaw
    import subprocess
    try:
        result = subprocess.run(["openclaw", "--version"], 
                              capture_output=True, text=True)
        print(f"✅ OpenClaw: {result.stdout.strip()}")
    except Exception as e:
        print(f"⚠ OpenClaw check: {e}")
    
    # Run test
    try:
        success = asyncio.run(run_single_task())
        
        if success:
            print("\n🎉 Test completed successfully!")
            print("\n🚀 Next steps:")
            print("1. Run full benchmark with: clawarena run --agent openclaw:agent_id=claude")
            print("2. Test more tasks: clawarena list tasks")
            print("3. Compare agents: clawarena run --agent openclaw:agent_id=claude --agent dummy")
        else:
            print("\n⚠ Test had issues. Check the output above.")
            
    except KeyboardInterrupt:
        print("\n\n⏹ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()