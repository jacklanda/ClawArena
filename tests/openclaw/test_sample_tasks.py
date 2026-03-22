#!/usr/bin/env python3
"""
Test OpenClaw on a sample of ClawArena tasks.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_sample_tasks():
    """Test OpenClaw on a sample of tasks."""
    print("🧪 Testing OpenClaw on Sample ClawArena Tasks")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    from clawarena.tasks.registry import TaskRegistry
    
    # Load all tasks
    registry = TaskRegistry()
    all_tasks = registry.list_all()
    
    # Take a sample of 3 tasks (one from each main category)
    sample_tasks = []
    categories_seen = set()
    
    for task in all_tasks:
        if task.category.value not in categories_seen:
            sample_tasks.append(task)
            categories_seen.add(task.category.value)
        
        if len(sample_tasks) >= 3:
            break
    
    print(f"📋 Testing {len(sample_tasks)} sample tasks:")
    for task in sample_tasks:
        print(f"  - {task.name} ({task.category.value}, {task.difficulty.value})")
        print(f"    Instruction: {task.instruction[:80]}...")
    
    # Get adapters
    adapter_registry = AdapterRegistry()
    
    print("\n📦 Loading adapters...")
    adapters = []
    
    # Dummy adapter for baseline
    dummy = adapter_registry.get("dummy")
    adapters.append(dummy)
    print(f"  ✅ {dummy.info().name} (baseline)")
    
    # OpenClaw adapter
    try:
        openclaw = adapter_registry.get("openclaw", agent_id="main")
        adapters.append(openclaw)
        print(f"  ✅ {openclaw.info().name}")
    except Exception as e:
        print(f"  ❌ OpenClaw adapter failed: {e}")
        return False
    
    # Create suite
    suite = TaskSuite(
        name="Sample Tasks Test",
        description="Test on sample of ClawArena tasks",
        tasks=sample_tasks
    )
    
    print(f"\n🚀 Executing {len(sample_tasks)} tasks with {len(adapters)} adapters...")
    
    # Run tasks
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    results = await engine.run(suite, adapters)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 Detailed Results")
    print("=" * 60)
    
    for run_result in results:
        print(f"\n🔧 Agent: {run_result.agent.name}")
        print(f"   Overall Score: {run_result.aggregate_score:.2f}/100")
        print(f"   Total Duration: {run_result.total_duration_seconds:.2f}s")
        print(f"   Total Tokens: {run_result.total_tokens.total_tokens}")
        print(f"   Total Cost: ${run_result.total_cost.total_cost_usd:.6f}")
        
        for i, task_result in enumerate(run_result.task_results, 1):
            print(f"\n   📋 Task {i}: {task_result.task_name}")
            print(f"      Category: {task_result.task_id.split('.')[0]}")
            print(f"      Score: {task_result.score.overall:.2f}/100")
            print(f"      Passed: {'✅' if task_result.passed else '❌'}")
            
            response = task_result.agent_response
            if response.error:
                print(f"      ❌ Error: {response.error[:200]}...")
            else:
                # Show response preview
                output_preview = response.output
                if len(output_preview) > 150:
                    output_preview = output_preview[:150] + "..."
                print(f"      📝 Response: {output_preview}")
    
    # Performance comparison
    print("\n" + "=" * 60)
    print("⚡ Performance Comparison")
    print("=" * 60)
    
    from clawarena.core.scoring import Leaderboard
    leaderboard = Leaderboard.from_runs(results)
    
    print("\nRank | Agent           | Score  | Duration | Tokens | Cost      | Success")
    print("-" * 70)
    
    for entry in leaderboard.entries:
        success_rate = (entry.tasks_passed / entry.tasks_total * 100) if entry.tasks_total > 0 else 0
        print(f"{entry.rank:4} | {entry.agent_name:15} | {entry.overall_score:6.2f} | "
              f"{entry.avg_duration_seconds:8.2f}s | {entry.total_tokens:6} | "
              f"${entry.total_cost_usd:8.6f} | {success_rate:6.1f}%")
    
    # Task-by-task analysis
    print("\n" + "=" * 60)
    print("📈 Task-by-Task Analysis")
    print("=" * 60)
    
    # For each task, compare agent performance
    for i, task in enumerate(sample_tasks, 1):
        print(f"\nTask {i}: {task.name}")
        print(f"Category: {task.category.value}, Difficulty: {task.difficulty.value}")
        
        for run_result in results:
            task_result = run_result.task_results[i-1]  # Same order as tasks
            response = task_result.agent_response
            
            print(f"  {run_result.agent.name}:")
            print(f"    Score: {task_result.score.overall:.2f}")
            print(f"    Duration: {response.duration_seconds:.2f}s")
            print(f"    Tokens: {response.token_usage.total_tokens}")
            
            if response.error:
                print(f"    Status: ❌ Error")
            else:
                print(f"    Status: ✅ Success")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("🎯 Recommendations")
    print("=" * 60)
    
    if len(results) >= 2:
        openclaw_result = results[1]  # Assuming OpenClaw is second
        dummy_result = results[0]     # Assuming Dummy is first
        
        openclaw_score = openclaw_result.aggregate_score
        dummy_score = dummy_result.aggregate_score
        
        if openclaw_score > dummy_score:
            print("✅ OpenClaw outperforms Dummy adapter!")
            improvement = ((openclaw_score - dummy_score) / dummy_score * 100) if dummy_score > 0 else 100
            print(f"   Improvement: +{improvement:.1f}%")
        elif openclaw_score < dummy_score:
            print("⚠ OpenClaw underperforms compared to Dummy adapter")
            difference = dummy_score - openclaw_score
            print(f"   Difference: -{difference:.2f} points")
        else:
            print("📊 OpenClaw performs equally to Dummy adapter")
        
        # Cost analysis
        openclaw_cost = openclaw_result.total_cost.total_cost_usd
        if openclaw_cost > 0:
            cost_per_point = openclaw_cost / openclaw_score if openclaw_score > 0 else 0
            print(f"💰 Cost per point: ${cost_per_point:.6f}")
        
        # Success rate
        openclaw_success = sum(1 for tr in openclaw_result.task_results if not tr.error)
        openclaw_total = len(openclaw_result.task_results)
        openclaw_success_rate = (openclaw_success / openclaw_total * 100) if openclaw_total > 0 else 0
        
        dummy_success = sum(1 for tr in dummy_result.task_results if not tr.error)
        dummy_total = len(dummy_result.task_results)
        dummy_success_rate = (dummy_success / dummy_total * 100) if dummy_total > 0 else 0
        
        print(f"✅ Success rate: OpenClaw {openclaw_success_rate:.1f}% vs Dummy {dummy_success_rate:.1f}%")
    
    print("\n✅ Sample test completed!")
    return True

def main():
    """Main entry point."""
    print("🎯 OpenClaw Performance Test on Sample Tasks")
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
    
    print("\nThis test will run 3 sample tasks from different categories.")
    print("Estimated time: 1-2 minutes")
    print("Estimated cost: < $0.005")
    
    print("\nStarting test...")
    
    try:
        success = asyncio.run(test_sample_tasks())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Sample Test Completed!")
            print("=" * 60)
            print("\nOpenClaw adapter performance has been evaluated.")
            print("Check the results above for detailed metrics.")
            
        else:
            print("\n⚠ Test had issues.")
            
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