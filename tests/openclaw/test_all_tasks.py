#!/usr/bin/env python3
"""
Test OpenClaw adapter on all ClawArena tasks.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_all_tasks():
    """Test OpenClaw on all available tasks."""
    print("🧪 Testing OpenClaw on All ClawArena Tasks")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    from clawarena.tasks.registry import TaskRegistry
    
    # Load all tasks
    registry = TaskRegistry()
    all_tasks = registry.list_all()
    
    print(f"📋 Found {len(all_tasks)} tasks:")
    
    # Group by category
    categories = {}
    for task in all_tasks:
        category = task.category.value
        if category not in categories:
            categories[category] = []
        categories[category].append(task)
    
    for category, tasks in categories.items():
        print(f"  {category}: {len(tasks)} tasks")
        for task in tasks:
            print(f"    - {task.name} ({task.difficulty.value})")
    
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
    
    # Test by category
    print("\n" + "=" * 60)
    print("🚀 Starting Category Tests")
    print("=" * 60)
    
    all_results = []
    
    for category, tasks in categories.items():
        print(f"\n📊 Testing {category.upper()} category ({len(tasks)} tasks)")
        print("-" * 40)
        
        # Create suite for this category
        suite = TaskSuite(
            name=f"{category.capitalize()} Tasks",
            description=f"Tasks from {category} category",
            tasks=tasks
        )
        
        # Run tasks
        engine = RunEngine(evaluator_registry=get_evaluator_registry())
        print(f"Executing {len(tasks)} tasks with {len(adapters)} adapters...")
        
        try:
            results = await engine.run(suite, adapters)
            all_results.extend(results)
            
            # Show category results
            for run_result in results:
                successful = sum(1 for tr in run_result.task_results if not tr.error)
                total = len(run_result.task_results)
                
                print(f"  {run_result.agent.name}: {successful}/{total} successful, "
                      f"score: {run_result.aggregate_score:.2f}, "
                      f"cost: ${run_result.total_cost.total_cost_usd:.6f}")
                
        except Exception as e:
            print(f"  ❌ Error in {category} category: {e}")
    
    # Overall analysis
    print("\n" + "=" * 60)
    print("📈 Overall Performance Analysis")
    print("=" * 60)
    
    from clawarena.core.scoring import Leaderboard
    leaderboard = Leaderboard.from_runs(all_results)
    
    print("\n🏆 Overall Leaderboard:")
    print("-" * 60)
    print("Rank | Agent           | Score  | Tasks | Success | Cost      | Avg Time")
    print("-" * 60)
    
    for entry in leaderboard.entries:
        success_rate = (entry.tasks_passed / entry.tasks_total * 100) if entry.tasks_total > 0 else 0
        print(f"{entry.rank:4} | {entry.agent_name:15} | {entry.overall_score:6.2f} | "
              f"{entry.tasks_total:5} | {success_rate:6.1f}% | "
              f"${entry.total_cost_usd:8.6f} | {entry.avg_duration_seconds:7.2f}s")
    
    # Detailed breakdown by category
    print("\n" + "=" * 60)
    print("📊 Category Performance Breakdown")
    print("=" * 60)
    
    # Re-analyze by category
    for category, tasks in categories.items():
        print(f"\n{category.upper()} Category:")
        
        # Filter results for this category
        category_task_ids = {t.id for t in tasks}
        category_results = []
        
        for run_result in all_results:
            category_task_results = [
                tr for tr in run_result.task_results 
                if tr.task_id in category_task_ids
            ]
            if category_task_results:
                # Calculate category-specific metrics
                successful = sum(1 for tr in category_task_results if not tr.error)
                total = len(category_task_results)
                avg_score = sum(tr.score.overall for tr in category_task_results) / total if total > 0 else 0
                
                print(f"  {run_result.agent.name}: {successful}/{total} successful, "
                      f"avg score: {avg_score:.2f}")
    
    # Cost analysis
    print("\n" + "=" * 60)
    print("💰 Cost Analysis")
    print("=" * 60)
    
    total_tasks = sum(len(cat_tasks) for cat_tasks in categories.values())
    total_runs = len(all_results)
    
    openclaw_results = [r for r in all_results if "OpenClaw" in r.agent.name]
    dummy_results = [r for r in all_results if "Dummy" in r.agent.name]
    
    if openclaw_results:
        openclaw_result = openclaw_results[0]
        openclaw_cost = openclaw_result.total_cost.total_cost_usd
        openclaw_tasks = len(openclaw_result.task_results)
        avg_cost_per_task = openclaw_cost / openclaw_tasks if openclaw_tasks > 0 else 0
        
        print(f"OpenClaw total cost: ${openclaw_cost:.6f}")
        print(f"OpenClaw tasks executed: {openclaw_tasks}")
        print(f"Average cost per task: ${avg_cost_per_task:.6f}")
    
    if dummy_results:
        dummy_result = dummy_results[0]
        print(f"\nDummy total cost: ${dummy_result.total_cost.total_cost_usd:.6f}")
        print(f"Dummy tasks executed: {len(dummy_result.task_results)}")
    
    # Success rate analysis
    print("\n" + "=" * 60)
    print("✅ Success Rate Analysis")
    print("=" * 60)
    
    for run_result in all_results:
        successful = sum(1 for tr in run_result.task_results if not tr.error)
        total = len(run_result.task_results)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"{run_result.agent.name}:")
        print(f"  Success rate: {success_rate:.1f}% ({successful}/{total})")
        
        # List failed tasks if any
        failed_tasks = [tr for tr in run_result.task_results if tr.error]
        if failed_tasks:
            print(f"  Failed tasks: {len(failed_tasks)}")
            for ft in failed_tasks[:3]:  # Show first 3 failures
                print(f"    - {ft.task_name}: {ft.error[:100]}...")
            if len(failed_tasks) > 3:
                print(f"    ... and {len(failed_tasks) - 3} more")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("🎯 Recommendations")
    print("=" * 60)
    
    if openclaw_results:
        openclaw_result = openclaw_results[0]
        openclaw_score = openclaw_result.aggregate_score
        dummy_score = dummy_results[0].aggregate_score if dummy_results else 0
        
        if openclaw_score > dummy_score:
            print("✅ OpenClaw outperforms Dummy adapter!")
        elif openclaw_score < dummy_score:
            print("⚠ OpenClaw underperforms compared to Dummy adapter")
        else:
            print("📊 OpenClaw performs equally to Dummy adapter")
        
        # Check cost-effectiveness
        if openclaw_result.total_cost.total_cost_usd > 0.01:  # More than 1 cent
            print("💰 OpenClaw has measurable cost - consider optimizing task complexity")
        else:
            print("💰 OpenClaw cost is minimal - good for frequent testing")
    
    print("\n✅ Testing completed!")
    return True

def main():
    """Main entry point."""
    print("🎯 OpenClaw Performance Test on All ClawArena Tasks")
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
    
    print("\n⚠ Warning: This will execute all 10 ClawArena tasks.")
    print("   This may take several minutes and use API credits.")
    print("   Estimated cost: < $0.01")
    
    print("\nStarting test...")
    
    try:
        success = asyncio.run(test_all_tasks())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 All Tasks Test Completed!")
            print("=" * 60)
            print("\nOpenClaw adapter has been tested on all ClawArena tasks.")
            print("Check the results above for performance metrics.")
            
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