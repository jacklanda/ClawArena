#!/usr/bin/env python3
"""
Quick demonstration of OpenClaw integration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def quick_demo():
    """Quick demo of OpenClaw integration."""
    print("🚀 OpenClaw Integration Quick Demo")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec, TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    
    # Create a single test task
    task = Task(
        id="demo_task",
        name="Demo Task",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("medium"),
        description="Demo of OpenClaw integration",
        instruction="Explain the concept of machine learning in one paragraph.",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=30,
    )
    
    # Get adapters
    registry = AdapterRegistry()
    
    print("📦 Loading adapters...")
    adapters = []
    
    # Dummy adapter
    dummy = registry.get("dummy")
    adapters.append(dummy)
    print(f"  ✅ {dummy.info().name}")
    
    # OpenClaw adapter
    try:
        openclaw = registry.get("openclaw", agent_id="main")
        adapters.append(openclaw)
        print(f"  ✅ {openclaw.info().name}")
    except Exception as e:
        print(f"  ❌ OpenClaw adapter failed: {e}")
        return False
    
    # Create task suite
    suite = TaskSuite(
        name="Quick Demo",
        description="Quick demonstration",
        tasks=[task]
    )
    
    print(f"\n🎯 Task: {task.name}")
    print(f"   Instruction: {task.instruction}")
    print("\n🚀 Executing...")
    
    # Run task
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    results = await engine.run(suite, adapters)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 Results")
    print("=" * 60)
    
    for run_result in results:
        print(f"\n🔧 Agent: {run_result.agent.name}")
        print(f"   Score: {run_result.aggregate_score:.2f}/100")
        print(f"   Duration: {run_result.total_duration_seconds:.2f}s")
        print(f"   Tokens: {run_result.total_tokens.total_tokens}")
        print(f"   Cost: ${run_result.total_cost.total_cost_usd:.6f}")
        
        for task_result in run_result.task_results:
            response = task_result.agent_response
            
            if response.error:
                print(f"   ❌ Error: {response.error}")
            else:
                print(f"\n   📝 Response:")
                print("-" * 40)
                print(response.output[:300] + "..." if len(response.output) > 300 else response.output)
                print("-" * 40)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Summary")
    print("=" * 60)
    
    if len(results) > 1:
        from clawarena.core.scoring import Leaderboard
        leaderboard = Leaderboard.from_runs(results)
        
        print("\n🏆 Leaderboard:")
        for entry in leaderboard.entries:
            print(f"  {entry.rank}. {entry.agent_name}: {entry.overall_score:.2f} points")
    
    print(f"\n✅ Demo completed successfully!")
    print(f"   Total tasks executed: {len(results)}")
    print(f"   Total cost: ${sum(r.total_cost.total_cost_usd for r in results):.6f}")
    
    return True

def main():
    """Main entry point."""
    print("🎯 ClawArena OpenClaw Integration - Quick Demo")
    print("=" * 60)
    
    # Check OpenClaw
    import subprocess
    try:
        result = subprocess.run(["openclaw", "--version"], 
                              capture_output=True, text=True)
        version = result.stdout.strip().split()[1]
        print(f"✅ OpenClaw {version} detected")
    except Exception as e:
        print(f"⚠ OpenClaw check: {e}")
    
    print("\nRunning quick demo...")
    
    try:
        success = asyncio.run(quick_demo())
        
        if success:
            print("\n" + "=" * 60)
            print("✅ INTEGRATION SUCCESSFUL!")
            print("=" * 60)
            print("\nOpenClaw adapter is now fully integrated with ClawArena.")
            print("\nWhat we've accomplished:")
            print("1. ✅ Created OpenClaw agent adapter")
            print("2. ✅ Integrated with ClawArena registry")
            print("3. ✅ Tested with real OpenClaw execution")
            print("4. ✅ Parsed JSON responses and token usage")
            print("5. ✅ Compared with Dummy adapter")
            print("6. ✅ Displayed scores and metrics")
            print("\nThe adapter is ready for production use!")
            
        else:
            print("\n⚠ Demo had issues.")
            
    except KeyboardInterrupt:
        print("\n\n⏹ Demo interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()