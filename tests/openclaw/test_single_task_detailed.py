#!/usr/bin/env python3
"""
Test OpenClaw on a single ClawArena task with detailed output.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_single_task():
    """Test OpenClaw on a single task with detailed analysis."""
    print("🧪 Testing OpenClaw on Single ClawArena Task")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    from clawarena.tasks.registry import TaskRegistry
    
    # Load tasks
    registry = TaskRegistry()
    all_tasks = registry.list_all()
    
    # Select the first task (email composition - usually easiest)
    task = None
    for t in all_tasks:
        if t.category.value == "email" and t.difficulty.value == "easy":
            task = t
            break
    
    if not task:
        task = all_tasks[0]  # Fallback to first task
    
    print(f"📋 Selected task: {task.name}")
    print(f"   Category: {task.category.value}")
    print(f"   Difficulty: {task.difficulty.value}")
    print(f"   Timeout: {task.timeout_seconds}s")
    print(f"\n📝 Instruction:")
    print("-" * 40)
    print(task.instruction)
    print("-" * 40)
    
    if task.context:
        print(f"\n📚 Context: {task.context}")
    
    # Get adapters
    adapter_registry = AdapterRegistry()
    
    print("\n📦 Loading adapters...")
    adapters = []
    
    # Dummy adapter for baseline
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
        name="Single Task Test",
        description="Test on single ClawArena task",
        tasks=[task]
    )
    
    print(f"\n🚀 Executing task...")
    
    # Run task
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    results = await engine.run(suite, adapters)
    
    # Detailed analysis
    print("\n" + "=" * 60)
    print("📊 Detailed Analysis")
    print("=" * 60)
    
    for run_result in results:
        print(f"\n🔧 Agent: {run_result.agent.name}")
        print(f"   Model: {run_result.agent.model}")
        print(f"   Description: {run_result.agent.description[:100]}...")
        
        task_result = run_result.task_results[0]
        response = task_result.agent_response
        
        print(f"\n   📋 Task Result:")
        print(f"      Score: {task_result.score.overall:.2f}/100")
        print(f"      Passed: {'✅' if task_result.passed else '❌'}")
        
        # Score breakdown
        print(f"\n   📈 Score Breakdown:")
        print(f"      Correctness: {task_result.score.correctness:.2f}/40")
        print(f"      Completeness: {task_result.score.completeness:.2f}/25")
        print(f"      Efficiency: {task_result.score.efficiency:.2f}/20")
        print(f"      Robustness: {task_result.score.robustness:.2f}/15")
        
        print(f"\n   ⚡ Performance Metrics:")
        print(f"      Duration: {response.duration_seconds:.2f}s")
        print(f"      API Calls: {response.api_calls}")
        print(f"      Input Tokens: {response.token_usage.input_tokens}")
        print(f"      Output Tokens: {response.token_usage.output_tokens}")
        print(f"      Total Tokens: {response.token_usage.total_tokens}")
        print(f"      Cost: ${task_result.cost.total_cost_usd:.6f}")
        
        if response.error:
            print(f"\n   ❌ Error: {response.error}")
        else:
            print(f"\n   📝 Full Response:")
            print("-" * 40)
            print(response.output)
            print("-" * 40)
            
            # Response analysis
            print(f"\n   📊 Response Analysis:")
            print(f"      Length: {len(response.output)} characters")
            print(f"      Lines: {response.output.count(chr(10)) + 1}")
            
            # Check for common email elements (if email task)
            if task.category.value == "email":
                email_checks = [
                    ("Subject line", "Subject:" in response.output or "SUBJECT:" in response.output),
                    ("Greeting", any(g in response.output for g in ["Dear", "Hello", "Hi", "Greetings"])),
                    ("Closing", any(c in response.output for c in ["Sincerely", "Best regards", "Regards", "Thank you"])),
                    ("Signature", any(s in response.output for s in ["[Your Name]", "Name:", "Signature:"])),
                ]
                
                print(f"      Email elements found:")
                for element, found in email_checks:
                    print(f"        {'✅' if found else '❌'} {element}")
        
        # Trace information
        if response.trace:
            print(f"\n   🔍 Execution Trace:")
            for trace_item in response.trace[:3]:  # Show first 3 trace items
                print(f"      Step: {trace_item.get('step', 'unknown')}")
                for key, value in trace_item.items():
                    if key != 'step':
                        print(f"        {key}: {value}")
    
    # Comparison
    print("\n" + "=" * 60)
    print("⚡ Agent Comparison")
    print("=" * 60)
    
    if len(results) >= 2:
        dummy_result = results[0]
        openclaw_result = results[1]
        
        dummy_task = dummy_result.task_results[0]
        openclaw_task = openclaw_result.task_results[0]
        
        print("\nMetric           | DummyAgent     | OpenClaw       | Difference")
        print("-" * 60)
        
        metrics = [
            ("Score", dummy_task.score.overall, openclaw_task.score.overall, "points"),
            ("Duration (s)", dummy_task.agent_response.duration_seconds, 
             openclaw_task.agent_response.duration_seconds, "seconds"),
            ("Tokens", dummy_task.agent_response.token_usage.total_tokens,
             openclaw_task.agent_response.token_usage.total_tokens, "tokens"),
            ("Cost ($)", dummy_task.cost.total_cost_usd,
             openclaw_task.cost.total_cost_usd, "dollars"),
        ]
        
        for name, dummy_val, openclaw_val, unit in metrics:
            diff = openclaw_val - dummy_val
            diff_str = f"+{diff:.4f}" if diff >= 0 else f"{diff:.4f}"
            print(f"{name:15} | {dummy_val:12.4f} | {openclaw_val:12.4f} | {diff_str} {unit}")
        
        # Quality assessment
        print(f"\n🎯 Quality Assessment:")
        
        if openclaw_task.score.overall > dummy_task.score.overall:
            improvement = ((openclaw_task.score.overall - dummy_task.score.overall) / dummy_task.score.overall * 100)
            print(f"✅ OpenClaw outperforms Dummy by {improvement:.1f}%")
        elif openclaw_task.score.overall < dummy_task.score.overall:
            difference = dummy_task.score.overall - openclaw_task.score.overall
            print(f"⚠ OpenClaw underperforms by {difference:.2f} points")
        else:
            print(f"📊 Both agents performed equally")
        
        # Cost-effectiveness
        if openclaw_task.cost.total_cost_usd > 0:
            cost_per_point = openclaw_task.cost.total_cost_usd / openclaw_task.score.overall if openclaw_task.score.overall > 0 else 0
            print(f"💰 Cost per point: ${cost_per_point:.6f}")
        
        # Response quality comparison
        print(f"\n📝 Response Quality:")
        dummy_len = len(dummy_task.agent_response.output)
        openclaw_len = len(openclaw_task.agent_response.output)
        
        print(f"  Dummy response length: {dummy_len} chars")
        print(f"  OpenClaw response length: {openclaw_len} chars")
        
        if openclaw_len > dummy_len * 2:
            print(f"  📈 OpenClaw provides more detailed response")
        elif openclaw_len < dummy_len:
            print(f"  📉 OpenClaw response is more concise")
        else:
            print(f"  📊 Response lengths are similar")
    
    print("\n✅ Single task test completed!")
    return True

def main():
    """Main entry point."""
    print("🎯 OpenClaw Detailed Test on Single Task")
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
    
    print("\nThis test will run a single ClawArena task with detailed analysis.")
    print("Estimated time: 30-60 seconds")
    print("Estimated cost: < $0.002")
    
    print("\nStarting test...")
    
    try:
        success = asyncio.run(test_single_task())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Detailed Test Completed!")
            print("=" * 60)
            print("\nOpenClaw adapter has been thoroughly tested.")
            print("Check the detailed analysis above.")
            
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