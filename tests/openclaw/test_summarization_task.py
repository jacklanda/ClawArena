#!/usr/bin/env python3
"""
Test OpenClaw on a summarization task.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_summarization():
    """Test OpenClaw on a summarization task."""
    print("🧪 Testing OpenClaw on Summarization Task")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    from clawarena.tasks.registry import TaskRegistry
    
    # Load tasks
    registry = TaskRegistry()
    all_tasks = registry.list_all()
    
    # Find a summarization task
    task = None
    for t in all_tasks:
        if t.category.value == "summarization" and t.difficulty.value == "easy":
            task = t
            break
    
    if not task:
        print("❌ No easy summarization task found")
        return False
    
    print(f"📋 Selected task: {task.name}")
    print(f"   Category: {task.category.value}")
    print(f"   Difficulty: {task.difficulty.value}")
    print(f"\n📝 Instruction preview:")
    print("-" * 40)
    instruction_preview = task.instruction[:200] + "..." if len(task.instruction) > 200 else task.instruction
    print(instruction_preview)
    print("-" * 40)
    
    # Get adapters
    adapter_registry = AdapterRegistry()
    
    print("\n📦 Loading adapters...")
    adapters = []
    
    # Dummy adapter
    dummy = adapter_registry.get("dummy")
    adapters.append(dummy)
    print(f"  ✅ {dummy.info().name}")
    
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
        name="Summarization Test",
        description="Test on summarization task",
        tasks=[task]
    )
    
    print(f"\n🚀 Executing summarization task...")
    
    # Run task
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    results = await engine.run(suite, adapters)
    
    # Results
    print("\n" + "=" * 60)
    print("📊 Results")
    print("=" * 60)
    
    for run_result in results:
        task_result = run_result.task_results[0]
        response = task_result.agent_response
        
        print(f"\n🔧 Agent: {run_result.agent.name}")
        print(f"   Score: {task_result.score.overall:.2f}/100")
        print(f"   Duration: {response.duration_seconds:.2f}s")
        print(f"   Tokens: {response.token_usage.total_tokens}")
        print(f"   Cost: ${task_result.cost.total_cost_usd:.6f}")
        
        if response.error:
            print(f"   ❌ Error: {response.error}")
        else:
            print(f"\n   📝 Summary:")
            print("-" * 40)
            # Show first 300 chars of summary
            summary_preview = response.output[:300] + "..." if len(response.output) > 300 else response.output
            print(summary_preview)
            print("-" * 40)
            
            # Analysis
            print(f"\n   📊 Summary Analysis:")
            print(f"      Length: {len(response.output)} characters")
            print(f"      Estimated word count: {len(response.output.split())} words")
    
    # Comparison
    if len(results) >= 2:
        print("\n" + "=" * 60)
        print("⚡ Comparison")
        print("=" * 60)
        
        dummy_result = results[0]
        openclaw_result = results[1]
        
        dummy_score = dummy_result.task_results[0].score.overall
        openclaw_score = openclaw_result.task_results[0].score.overall
        
        dummy_tokens = dummy_result.task_results[0].agent_response.token_usage.total_tokens
        openclaw_tokens = openclaw_result.task_results[0].agent_response.token_usage.total_tokens
        
        dummy_cost = dummy_result.task_results[0].cost.total_cost_usd
        openclaw_cost = openclaw_result.task_results[0].cost.total_cost_usd
        
        print(f"\nDummyAgent:")
        print(f"  Score: {dummy_score:.2f}, Tokens: {dummy_tokens}, Cost: ${dummy_cost:.6f}")
        
        print(f"\nOpenClaw-main:")
        print(f"  Score: {openclaw_score:.2f}, Tokens: {openclaw_tokens}, Cost: ${openclaw_cost:.6f}")
        
        # Quality assessment
        if openclaw_score > dummy_score:
            improvement = ((openclaw_score - dummy_score) / dummy_score * 100) if dummy_score > 0 else 100
            print(f"\n✅ OpenClaw outperforms by {improvement:.1f}%")
        elif openclaw_score < dummy_score:
            difference = dummy_score - openclaw_score
            print(f"\n⚠ OpenClaw underperforms by {difference:.2f} points")
        else:
            print(f"\n📊 Both agents performed equally")
        
        # Check if OpenClaw generated a real summary
        openclaw_output = openclaw_result.task_results[0].agent_response.output
        dummy_output = dummy_result.task_results[0].agent_response.output
        
        if len(openclaw_output) > len(dummy_output) * 1.5:
            print(f"📈 OpenClaw generated a more detailed summary")
        elif "Task '" in dummy_output and "' completed" in dummy_output:
            print(f"🎯 OpenClaw generated an actual summary, while Dummy just acknowledged the task")
    
    print("\n✅ Summarization test completed!")
    return True

def main():
    """Main entry point."""
    print("🎯 OpenClaw Test on Summarization Task")
    print("=" * 60)
    
    print("\nTesting OpenClaw on a meeting summarization task...")
    print("Estimated time: 30-60 seconds")
    
    try:
        success = asyncio.run(test_summarization())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Summarization Test Completed!")
            print("=" * 60)
            
        else:
            print("\n⚠ Test had issues.")
            
    except KeyboardInterrupt:
        print("\n\n⏹ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()