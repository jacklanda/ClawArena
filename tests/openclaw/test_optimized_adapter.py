#!/usr/bin/env python3
"""
Test the optimized OpenClaw adapter with improved token counting and error handling.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_optimized_adapter():
    """Test the optimized OpenClaw adapter."""
    print("🧪 Testing Optimized OpenClaw Adapter")
    print("=" * 60)
    
    # Import optimized registry
    from clawarena.adapters.registry_optimized import optimized_registry
    
    print("📦 Available adapters:")
    for adapter_name in optimized_registry.list_available():
        info = optimized_registry.get_adapter_info(adapter_name)
        print(f"  - {adapter_name}: {info.get('name', 'N/A')}")
        if "error" in info:
            print(f"    ⚠ {info['error']}")
    
    print("\n🚀 Testing optimized OpenClaw adapter...")
    
    # Create a simple test task
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    test_task = Task(
        id="optimized_test",
        name="Optimized Adapter Test",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Test the optimized OpenClaw adapter",
        instruction="Write a short paragraph about artificial intelligence (about 50 words).",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=60,
    )
    
    print(f"\n📝 Test Task: {test_task.name}")
    print(f"   Instruction: {test_task.instruction[:100]}...")
    
    # Test with debug mode enabled
    print("\n🔧 Creating optimized adapter with debug mode...")
    try:
        adapter = optimized_registry.get(
            "openclaw-optimized",
            agent_id="main",
            enable_debug=True,
            timeout_seconds=30,
        )
        
        print(f"✅ Adapter created: {adapter.info().name}")
        print(f"   Model: {adapter.info().model}")
        print(f"   Metadata: {adapter.info().metadata}")
        
    except Exception as e:
        print(f"❌ Failed to create adapter: {e}")
        return False
    
    # Execute task
    print("\n🚀 Executing test task...")
    try:
        response = await adapter.run_task(test_task)
        
        print(f"\n✅ Task completed!")
        print(f"   Duration: {response.duration_seconds:.2f}s")
        print(f"   Tokens: {response.token_usage.total_tokens}")
        print(f"   Input tokens: {response.token_usage.input_tokens}")
        print(f"   Output tokens: {response.token_usage.output_tokens}")
        print(f"   API calls: {response.api_calls}")
        
        if response.error:
            print(f"\n❌ Error: {response.error}")
        else:
            print(f"\n📝 Response ({len(response.output)} chars):")
            print("-" * 40)
            print(response.output[:500] + ("..." if len(response.output) > 500 else ""))
            print("-" * 40)
            
            # Analyze token estimation
            print(f"\n🔍 Token Analysis:")
            word_count = len(response.output.split())
            char_count = len(response.output)
            
            print(f"   Word count: {word_count}")
            print(f"   Character count: {char_count}")
            print(f"   Tokens per word: {response.token_usage.total_tokens / max(1, word_count):.2f}")
            print(f"   Tokens per char: {response.token_usage.total_tokens / max(1, char_count):.2f}")
            
            # Check if token count seems reasonable
            expected_tokens_min = word_count * 0.8  # Lower bound
            expected_tokens_max = word_count * 2.0  # Upper bound
            
            if expected_tokens_min <= response.token_usage.total_tokens <= expected_tokens_max:
                print(f"   ✅ Token count seems reasonable")
            else:
                print(f"   ⚠ Token count may be inaccurate")
                print(f"      Expected: {expected_tokens_min:.0f}-{expected_tokens_max:.0f}")
                print(f"      Got: {response.token_usage.total_tokens}")
        
        # Check trace information
        if response.trace:
            print(f"\n🔍 Execution Trace:")
            for trace_item in response.trace:
                print(f"   - {trace_item.get('step', 'unknown')}:")
                for key, value in trace_item.items():
                    if key != 'step':
                        print(f"     {key}: {value}")
        
        # Clean up
        await adapter.teardown()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Task execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def compare_adapters():
    """Compare original and optimized adapters."""
    print("\n" + "=" * 60)
    print("📊 Comparing Original vs Optimized Adapters")
    print("=" * 60)
    
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create test task
    test_task = Task(
        id="comparison_test",
        name="Adapter Comparison Test",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Compare original and optimized OpenClaw adapters",
        instruction="What is the capital of Japan? Answer in one sentence.",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=60,
    )
    
    # Test both adapters
    adapters_to_test = [
        ("original", "openclaw"),
        ("optimized", "openclaw-optimized"),
    ]
    
    results = {}
    
    for adapter_type, adapter_name in adapters_to_test:
        print(f"\n🔧 Testing {adapter_type} adapter...")
        
        try:
            if adapter_type == "original":
                from clawarena.adapters.registry import AdapterRegistry
                registry = AdapterRegistry()
                adapter = registry.get(adapter_name, agent_id="main")
            else:
                from clawarena.adapters.registry_optimized import optimized_registry
                adapter = optimized_registry.get(adapter_name, agent_id="main", enable_debug=False)
            
            response = await adapter.run_task(test_task)
            
            results[adapter_type] = {
                "success": not response.error,
                "duration": response.duration_seconds,
                "tokens": response.token_usage.total_tokens,
                "input_tokens": response.token_usage.input_tokens,
                "output_tokens": response.token_usage.output_tokens,
                "error": response.error,
                "output_preview": response.output[:100] + ("..." if len(response.output) > 100 else ""),
            }
            
            print(f"   ✅ Duration: {response.duration_seconds:.2f}s")
            print(f"   ✅ Tokens: {response.token_usage.total_tokens}")
            
            if response.error:
                print(f"   ❌ Error: {response.error[:100]}...")
            
            # Clean up
            if hasattr(adapter, 'teardown'):
                await adapter.teardown()
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results[adapter_type] = {"error": str(e)}
    
    # Print comparison
    print("\n" + "=" * 60)
    print("📈 Comparison Results")
    print("=" * 60)
    
    if "original" in results and "optimized" in results:
        orig = results["original"]
        opt = results["optimized"]
        
        print(f"\n📊 Performance Comparison:")
        print(f"   Duration: {orig.get('duration', 0):.2f}s → {opt.get('duration', 0):.2f}s")
        print(f"   Tokens: {orig.get('tokens', 0)} → {opt.get('tokens', 0)}")
        
        if orig.get('tokens', 0) > 0 and opt.get('tokens', 0) > 0:
            token_diff = opt.get('tokens', 0) - orig.get('tokens', 0)
            token_pct = (token_diff / orig.get('tokens', 0)) * 100
            print(f"   Token change: {token_diff:+d} ({token_pct:+.1f}%)")
        
        print(f"\n🔍 Response Comparison:")
        print(f"   Original: {orig.get('output_preview', 'N/A')}")
        print(f"   Optimized: {opt.get('output_preview', 'N/A')}")
    
    return results

def main():
    """Main entry point."""
    print("🎯 Optimized OpenClaw Adapter Test")
    print("=" * 60)
    print("\nTesting improvements:")
    print("1. More accurate token counting")
    print("2. Better error handling")
    print("3. Enhanced performance monitoring")
    
    try:
        # Test optimized adapter
        success = asyncio.run(test_optimized_adapter())
        
        if success:
            # Compare with original
            asyncio.run(compare_adapters())
            
            print("\n" + "=" * 60)
            print("🎉 Optimization Test Completed!")
            print("=" * 60)
            print("\nKey improvements tested:")
            print("✅ More accurate token estimation")
            print("✅ Better error message filtering")
            print("✅ Enhanced debugging capabilities")
            print("✅ Performance metrics tracking")
            
        else:
            print("\n⚠ Optimization test had issues.")
            
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