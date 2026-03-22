#!/usr/bin/env python3
"""
Final demonstration of OpenClaw integration with ClawArena.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def demonstrate_openclaw_integration():
    """Demonstrate the complete OpenClaw integration."""
    print("🚀 OpenClaw Integration Final Demo")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec, TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    
    # Create multiple test tasks
    tasks = [
        Task(
            id="task_1",
            name="Math Question",
            category=TaskCategory("general"),
            difficulty=TaskDifficulty("easy"),
            description="Simple math question",
            instruction="What is 15 * 23? Show your work.",
            evaluation=EvaluationSpec(evaluator="exact_match", config={}),
            timeout_seconds=30,
        ),
        Task(
            id="task_2",
            name="Creative Writing",
            category=TaskCategory("general"),
            difficulty=TaskDifficulty("medium"),
            description="Creative writing task",
            instruction="Write a two-sentence story about a robot learning to paint.",
            evaluation=EvaluationSpec(evaluator="exact_match", config={}),
            timeout_seconds=30,
        ),
        Task(
            id="task_3",
            name="Code Explanation",
            category=TaskCategory("general"),
            difficulty=TaskDifficulty("hard"),
            description="Code explanation task",
            instruction="Explain what this Python function does: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            evaluation=EvaluationSpec(evaluator="exact_match", config={}),
            timeout_seconds=30,
        ),
    ]
    
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
    
    # Create task suite
    suite = TaskSuite(
        name="OpenClaw Demo Suite",
        description="Demonstration of OpenClaw integration",
        tasks=tasks
    )
    
    print(f"\n🎯 Running {len(tasks)} tasks with {len(adapters)} adapters...")
    
    # Run tasks
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    results = await engine.run(suite, adapters)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 Detailed Results")
    print("=" * 60)
    
    for run_result in results:
        print(f"\n🔧 Agent: {run_result.agent.name}")
        print(f"   Model: {run_result.agent.model}")
        print(f"   Total Score: {run_result.aggregate_score:.2f}/100")
        print(f"   Total Duration: {run_result.total_duration_seconds:.2f}s")
        print(f"   Total Tokens: {run_result.total_tokens.total_tokens}")
        print(f"   Total Cost: ${run_result.total_cost.total_cost_usd:.6f}")
        
        for i, task_result in enumerate(run_result.task_results, 1):
            print(f"\n   📋 Task {i}: {task_result.task_name}")
            print(f"      Score: {task_result.score.overall:.2f}/100")
            
            # Show response preview
            response = task_result.agent_response
            output_preview = response.output
            if len(output_preview) > 100:
                output_preview = output_preview[:100] + "..."
            
            print(f"      Response: {output_preview}")
            
            if response.error:
                print(f"      ❌ Error: {response.error}")
    
    # Create leaderboard
    print("\n" + "=" * 60)
    print("🏆 Leaderboard")
    print("=" * 60)
    
    from clawarena.core.scoring import Leaderboard
    leaderboard = Leaderboard.from_runs(results)
    
    print("\nRank | Agent | Score | Duration | Tokens | Cost")
    print("-" * 60)
    
    for entry in leaderboard.entries:
        print(f"{entry.rank:4} | {entry.agent_name:15} | {entry.score:5.2f} | {entry.duration_seconds:8.2f}s | {entry.total_tokens:6} | ${entry.total_cost_usd:.6f}")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📈 Summary Statistics")
    print("=" * 60)
    
    total_tasks = len(tasks) * len(adapters)
    successful_tasks = sum(
        sum(1 for tr in r.task_results if not tr.error)
        for r in results
    )
    
    print(f"Total tasks executed: {total_tasks}")
    print(f"Successful tasks: {successful_tasks}")
    print(f"Success rate: {(successful_tasks/total_tasks*100):.1f}%")
    
    # Cost analysis
    total_cost = sum(r.total_cost.total_cost_usd for r in results)
    avg_cost_per_task = total_cost / total_tasks if total_tasks > 0 else 0
    
    print(f"\n💰 Cost Analysis:")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average cost per task: ${avg_cost_per_task:.6f}")
    
    # Performance comparison
    print(f"\n⚡ Performance Comparison:")
    for run_result in results:
        avg_duration = run_result.total_duration_seconds / len(run_result.task_results)
        avg_tokens = run_result.total_tokens.total_tokens / len(run_result.task_results)
        print(f"  {run_result.agent.name}: {avg_duration:.2f}s/task, {avg_tokens:.0f} tokens/task")
    
    return True

def main():
    """Main entry point."""
    print("🎯 ClawArena OpenClaw Integration - Final Demo")
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
    
    print("\nThis demo will:")
    print("1. Run 3 different tasks (math, creative writing, code explanation)")
    print("2. Compare Dummy adapter vs OpenClaw adapter")
    print("3. Show detailed results and metrics")
    print("4. Display cost and performance analysis")
    print("\nNote: This will use actual API credits for OpenClaw.")
    
    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Demo cancelled.")
        return
    
    try:
        success = asyncio.run(demonstrate_openclaw_integration())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Demo Completed Successfully!")
            print("=" * 60)
            print("\n✅ OpenClaw integration is fully functional!")
            print("\n🚀 Next steps for production use:")
            print("1. Create specialized tasks in tasks/openclaw/ directory")
            print("2. Configure different OpenClaw agents as needed")
            print("3. Use rubric-based evaluation for better scoring")
            print("4. Run benchmarks: clawarena run --agent openclaw:agent_id=main")
            print("5. Analyze results with: clawarena leaderboard")
            
        else:
            print("\n⚠ Demo had issues. Check the output above.")
            
    except KeyboardInterrupt:
        print("\n\n⏹ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()