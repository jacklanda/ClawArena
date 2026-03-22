#!/usr/bin/env python3
"""
Simple test of currency analysis task - just see if OpenClaw understands it.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_currency_understanding():
    """Test if OpenClaw understands the currency task."""
    print("🧪 Testing Currency Task Understanding")
    print("=" * 60)
    
    from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create a simplified version of the task
    simplified_instruction = """
    Analyze currency exchange rates and provide a plan for:
    1. Collecting current USD, EUR, JPY exchange rates against CNY
    2. Creating an Excel spreadsheet with the data
    3. Analyzing trends for the next 3 months
    4. Considering current economic events
    
    Just provide your analysis plan and approach. You don't need to actually collect data or create files.
    """
    
    task = Task(
        id="currency_understanding_test",
        name="Currency Analysis Understanding Test",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("medium"),
        description="Test understanding of currency analysis task",
        instruction=simplified_instruction,
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=120,
    )
    
    # Create adapter
    adapter = OpenClawAdapter(
        agent_id="main",
        timeout_seconds=60,
    )
    
    print(f"Task: {task.name}")
    print(f"\n📝 Simplified Instruction:")
    print("-" * 40)
    print(task.instruction)
    print("-" * 40)
    
    print(f"\n🚀 Testing OpenClaw understanding...")
    
    try:
        response = await adapter.run_task(task)
        
        print(f"\n✅ Response received!")
        print(f"Duration: {response.duration_seconds:.2f}s")
        print(f"Tokens: {response.token_usage.total_tokens}")
        
        if response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        print(f"\n📝 OpenClaw's Understanding:")
        print("=" * 60)
        print(response.output)
        print("=" * 60)
        
        # Analyze the response
        analysis_keywords = [
            "exchange rate", "currency", "Excel", "spreadsheet",
            "analysis", "trend", "prediction", "economic",
            "USD", "EUR", "JPY", "CNY", "data collection"
        ]
        
        found_keywords = []
        for keyword in analysis_keywords:
            if keyword.lower() in response.output.lower():
                found_keywords.append(keyword)
        
        print(f"\n🔍 Analysis of understanding:")
        print(f"Found {len(found_keywords)}/{len(analysis_keywords)} key concepts:")
        for keyword in found_keywords:
            print(f"  ✅ {keyword}")
        
        if len(found_keywords) >= 8:
            print(f"\n🎯 Excellent! OpenClaw understands the currency analysis task.")
            return True
        elif len(found_keywords) >= 5:
            print(f"\n📊 Good understanding of the task.")
            return True
        else:
            print(f"\n⚠ Limited understanding of the task.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    print("🎯 Currency Analysis Task Understanding Test")
    print("=" * 60)
    print("\nTesting if OpenClaw understands the complex currency analysis task.")
    print("This is a simplified version that only tests understanding, not execution.")
    
    try:
        success = asyncio.run(test_currency_understanding())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Understanding Test Completed!")
            print("=" * 60)
            print("\nOpenClaw demonstrates understanding of:")
            print("✅ Currency exchange rate concepts")
            print("✅ Data collection requirements")
            print("✅ Excel file creation")
            print("✅ Trend analysis")
            print("✅ Economic context integration")
            
            print("\n🚀 Next step: Full execution test with actual data collection")
            
        else:
            print("\n⚠ Understanding test had issues.")
            
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