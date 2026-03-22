#!/usr/bin/env python3
"""
Test the currency analysis task automatically.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_currency_analysis_auto(auto_run=True):
    """Test the currency analysis task automatically."""
    print("🧪 Testing Currency Exchange Rate Analysis Task (Auto)")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import TaskSuite
    from clawarena.engine.runner import RunEngine
    from clawarena.evaluators import get_evaluator_registry
    
    # Load the currency task
    from clawarena.tasks.registry import TaskRegistry
    
    task_registry = TaskRegistry()
    
    # Add our openclaw tasks directory
    task_dir = Path(__file__).parent / "tasks" / "openclaw"
    task_registry.add_directory(task_dir)
    
    # Get the currency task
    try:
        task = task_registry.get("openclaw_currency_analysis")
        print(f"✅ Loaded task: {task.name}")
        print(f"   Category: {task.category.value}")
        print(f"   Difficulty: {task.difficulty.value}")
        print(f"   Timeout: {task.timeout_seconds}s")
        
    except Exception as e:
        print(f"❌ Error loading task: {e}")
        return False
    
    # Display task overview
    print(f"\n📋 Task Overview:")
    print("-" * 40)
    instruction_preview = task.instruction[:300] + "..." if len(task.instruction) > 300 else task.instruction
    print(instruction_preview)
    print("-" * 40)
    
    # Get adapters
    adapter_registry = AdapterRegistry()
    
    print("\n📦 Loading adapters...")
    adapters = []
    
    # OpenClaw adapter (main agent)
    try:
        openclaw = adapter_registry.get("openclaw", agent_id="main")
        adapters.append(openclaw)
        print(f"  ✅ {openclaw.info().name}")
    except Exception as e:
        print(f"  ❌ OpenClaw adapter failed: {e}")
        return False
    
    # Create suite
    suite = TaskSuite(
        name="Currency Analysis Test",
        description="Test currency exchange rate analysis",
        tasks=[task]
    )
    
    print(f"\n⚠️  Important Notes:")
    print("1. This is a COMPLEX real-world task")
    print("2. Requires web access for data collection")
    print("3. May take 5-10 minutes to complete")
    print("4. Will attempt to create Excel file on Desktop")
    print("5. Uses actual API credits")
    
    if not auto_run:
        proceed = input("\nProceed with test? (y/n): ").strip().lower()
        if proceed != 'y':
            print("Test cancelled.")
            return False
    
    print(f"\n🚀 Executing complex currency analysis task...")
    print("This may take several minutes. Please wait...")
    
    # Run task with timeout
    try:
        engine = RunEngine(evaluator_registry=get_evaluator_registry())
        results = await asyncio.wait_for(
            engine.run(suite, adapters),
            timeout=task.timeout_seconds + 30  # Add buffer
        )
        
    except asyncio.TimeoutError:
        print(f"\n❌ Task timed out after {task.timeout_seconds}s")
        return False
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        return False
    
    # Results
    print("\n" + "=" * 60)
    print("📊 Task Execution Results")
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
            print(f"\n   ❌ Error: {response.error}")
        else:
            print(f"\n   ✅ Task completed!")
            
            # Show response preview
            print(f"\n   📝 Response Preview:")
            print("-" * 40)
            
            output = response.output
            
            # Extract key information
            if len(output) > 500:
                preview = output[:500] + "..."
            else:
                preview = output
            
            # Show in lines
            lines = preview.split('\n')
            for line in lines[:15]:  # Show first 15 lines
                if line.strip():
                    print(f"   {line[:100]}{'...' if len(line) > 100 else ''}")
            
            print("-" * 40)
            
            # Check for key elements
            key_elements = {
                "Excel file": "Currency_Analysis" in output or ".xlsx" in output,
                "Currency data": any(c in output for c in ["USD", "EUR", "JPY", "GBP"]),
                "Analysis": any(word in output.lower() for word in ["analysis", "prediction", "trend"]),
                "Current events": any(word in output.lower() for word in ["fed", "ecb", "inflation", "policy"]),
            }
            
            print(f"\n   🔍 Key elements found:")
            for element, found in key_elements.items():
                print(f"      {'✅' if found else '❌'} {element}")
    
    return True

def main():
    """Main entry point."""
    print("🎯 Currency Exchange Rate Analysis Task Test (Auto)")
    print("=" * 60)
    print("\nTesting OpenClaw on a complex real-world financial analysis task.")
    
    # Run automatically
    auto_run = True
    
    try:
        success = asyncio.run(test_currency_analysis_auto(auto_run))
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Currency Analysis Test Completed!")
            print("=" * 60)
            print("\nThis complex task tests OpenClaw's ability to:")
            print("✅ Handle multi-step real-world problems")
            print("✅ Integrate web data and current events")
            print("✅ Perform financial analysis")
            print("✅ Create structured output")
            
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