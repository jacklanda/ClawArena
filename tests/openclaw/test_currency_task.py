#!/usr/bin/env python3
"""
Test the currency analysis task with OpenClaw.
This is a complex real-world task that requires multiple capabilities.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_currency_analysis():
    """Test the currency analysis task."""
    print("🧪 Testing Currency Exchange Rate Analysis Task")
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
    
    # Display task details
    print(f"\n📋 Task Overview:")
    print("-" * 40)
    instruction_preview = task.instruction[:500] + "..." if len(task.instruction) > 500 else task.instruction
    print(instruction_preview)
    print("-" * 40)
    
    print(f"\n📚 Context provided:")
    if task.context:
        for key, value in task.context.items():
            if isinstance(value, list):
                print(f"  {key}: {', '.join(str(v) for v in value[:5])}...")
            elif isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")
    
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
    print("4. Will create Excel file on Desktop")
    print("5. Uses actual API credits")
    
    proceed = input("\nProceed with test? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Test cancelled.")
        return False
    
    print(f"\n🚀 Executing complex currency analysis task...")
    print("This may take several minutes. Please wait...")
    
    # Run task
    engine = RunEngine(evaluator_registry=get_evaluator_registry())
    results = await engine.run(suite, adapters)
    
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
            print(f"\n   ✅ Task completed successfully!")
            
            # Show response preview
            print(f"\n   📝 Response Preview:")
            print("-" * 40)
            
            # Try to extract key information from response
            output = response.output
            
            # Check for Excel file creation mention
            if "Currency_Analysis" in output or ".xlsx" in output:
                print("   Excel file creation mentioned in response")
            
            # Check for currency data
            currency_indicators = ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF"]
            found_currencies = [c for c in currency_indicators if c in output]
            if found_currencies:
                print(f"   Currency data found for: {', '.join(found_currencies[:3])}...")
            
            # Show analysis section if present
            analysis_keywords = ["analysis", "prediction", "trend", "forecast", "outlook"]
            if any(keyword in output.lower() for keyword in analysis_keywords):
                print("   Analysis/prediction section included")
            
            # Show preview of actual content
            lines = output.split('\n')
            preview_lines = []
            for line in lines[:20]:  # Show first 20 lines
                if line.strip():
                    preview_lines.append(f"   {line[:100]}{'...' if len(line) > 100 else ''}")
            
            if preview_lines:
                print("\n   Content preview:")
                for line in preview_lines[:10]:  # Show first 10 preview lines
                    print(line)
            
            print("-" * 40)
            
            # Check Desktop for created file
            print(f"\n   🔍 Checking Desktop for output file...")
            desktop_path = Path.home() / "Desktop"
            excel_files = list(desktop_path.glob("Currency_Analysis_*.xlsx"))
            
            if excel_files:
                print(f"   ✅ Found Excel file(s):")
                for file in excel_files:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"      - {file.name} ({size_mb:.2f} MB)")
            else:
                print(f"   ⚠ No Currency_Analysis Excel file found on Desktop")
                
                # Check for any recent Excel files
                recent_files = list(desktop_path.glob("*.xlsx"))
                if recent_files:
                    recent_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    print(f"   Recent Excel files on Desktop:")
                    for file in recent_files[:3]:
                        size_mb = file.stat().st_size / (1024 * 1024)
                        mtime = file.stat().st_mtime
                        from datetime import datetime
                        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                        print(f"      - {file.name} ({size_mb:.2f} MB, {mtime_str})")
    
    # Task complexity assessment
    print("\n" + "=" * 60)
    print("🎯 Task Complexity Assessment")
    print("=" * 60)
    
    print(f"\nThis task tests multiple capabilities:")
    print("1. 📊 Data Collection - Web scraping/fetching real-time data")
    print("2. 💾 Data Processing - Excel file creation and formatting")
    print("3. 📈 Financial Analysis - Trend analysis and predictions")
    print("4. 🌍 Current Events - Integration of global economic context")
    print("5. 🗂️ File Management - Desktop file creation and organization")
    
    print(f"\n✅ This is an excellent real-world test for OpenClaw agents!")
    print(f"   It simulates actual business intelligence tasks.")
    
    return True

def main():
    """Main entry point."""
    print("🎯 Currency Exchange Rate Analysis Task Test")
    print("=" * 60)
    print("\nTesting OpenClaw on a complex real-world financial analysis task.")
    print("The task requires:")
    print("1. Collecting real-time currency exchange rates")
    print("2. Creating an Excel spreadsheet")
    print("3. Performing 3-month trend analysis")
    print("4. Integrating current global events")
    print("5. Saving file to Desktop")
    
    try:
        success = asyncio.run(test_currency_analysis())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Currency Analysis Test Completed!")
            print("=" * 60)
            print("\nThis complex task tests OpenClaw's ability to:")
            print("✅ Handle multi-step real-world problems")
            print("✅ Integrate web data and current events")
            print("✅ Perform financial analysis")
            print("✅ Create structured output files")
            print("✅ Manage desktop file operations")
            
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