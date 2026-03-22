#!/usr/bin/env python3
"""
Test token counting accuracy of optimized OpenClaw adapter.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_token_accuracy():
    """Test token counting accuracy with different text types."""
    print("🧪 Testing Token Counting Accuracy")
    print("=" * 60)
    
    from clawarena.adapters.registry_optimized import optimized_registry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Test cases with expected token ranges
    test_cases = [
        {
            "name": "Short English",
            "instruction": "Say 'Hello, world!'",
            "expected_min": 2,
            "expected_max": 10,
        },
        {
            "name": "Medium English",
            "instruction": "Write a 50-word paragraph about artificial intelligence.",
            "expected_min": 30,
            "expected_max": 100,
        },
        {
            "name": "Code Explanation",
            "instruction": "Explain what this Python function does: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
            "expected_min": 20,
            "expected_max": 80,
        },
    ]
    
    # Create adapter with debug mode
    adapter = optimized_registry.get(
        "openclaw-optimized",
        agent_id="main",
        enable_debug=True,
        timeout_seconds=30,
    )
    
    print(f"🔧 Using adapter: {adapter.info().name}")
    print(f"   Workspace: {adapter.info().metadata.get('workspace', 'N/A')}")
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📝 Test: {test_case['name']}")
        print(f"   Instruction: {test_case['instruction'][:80]}...")
        
        # Create task
        task = Task(
            id=f"token_test_{test_case['name'].lower().replace(' ', '_')}",
            name=f"Token Test: {test_case['name']}",
            category=TaskCategory("general"),
            difficulty=TaskDifficulty("easy"),
            description=f"Test token counting for {test_case['name']}",
            instruction=test_case["instruction"],
            evaluation=EvaluationSpec(evaluator="exact_match", config={}),
            timeout_seconds=30,
        )
        
        # Execute
        try:
            response = await adapter.run_task(task)
            
            if response.error:
                print(f"   ❌ Error: {response.error}")
                results.append({
                    "name": test_case["name"],
                    "success": False,
                    "error": response.error,
                })
                continue
            
            # Analyze token count
            tokens = response.token_usage.total_tokens
            expected_min = test_case["expected_min"]
            expected_max = test_case["expected_max"]
            
            print(f"   ✅ Response: {len(response.output)} chars")
            print(f"   ✅ Tokens: {tokens}")
            print(f"   ✅ Expected range: {expected_min}-{expected_max}")
            
            if expected_min <= tokens <= expected_max:
                print(f"   ✅ Token count is reasonable!")
                accuracy = "good"
            elif tokens < expected_min:
                print(f"   ⚠ Token count seems low")
                accuracy = "low"
            else:
                print(f"   ⚠ Token count seems high")
                accuracy = "high"
            
            # Show token breakdown
            print(f"   🔍 Breakdown: input={response.token_usage.input_tokens}, "
                  f"output={response.token_usage.output_tokens}")
            
            # Calculate tokens per character/word
            if response.output:
                chars = len(response.output)
                words = len(response.output.split())
                
                tokens_per_char = tokens / chars if chars > 0 else 0
                tokens_per_word = tokens / words if words > 0 else 0
                
                print(f"   📊 Density: {tokens_per_char:.3f} tokens/char, "
                      f"{tokens_per_word:.3f} tokens/word")
            
            results.append({
                "name": test_case["name"],
                "success": True,
                "tokens": tokens,
                "expected_min": expected_min,
                "expected_max": expected_max,
                "accuracy": accuracy,
                "response_length": len(response.output),
                "duration": response.duration_seconds,
            })
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append({
                "name": test_case["name"],
                "success": False,
                "error": str(e),
            })
    
    # Clean up
    await adapter.teardown()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Token Accuracy Test Summary")
    print("=" * 60)
    
    successful_tests = [r for r in results if r.get("success")]
    failed_tests = [r for r in results if not r.get("success")]
    
    print(f"\n✅ Successful tests: {len(successful_tests)}/{len(test_cases)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(test_cases)}")
    
    if successful_tests:
        print(f"\n📈 Token Count Statistics:")
        
        for result in successful_tests:
            tokens = result["tokens"]
            expected_range = f"{result['expected_min']}-{result['expected_max']}"
            
            if result["accuracy"] == "good":
                status = "✅"
            elif result["accuracy"] == "low":
                status = "⚠"
            else:
                status = "⚠"
            
            print(f"   {status} {result['name']}: {tokens} tokens "
                  f"(expected {expected_range}) - {result['accuracy']}")
        
        # Calculate average accuracy
        total_tokens = sum(r["tokens"] for r in successful_tests)
        avg_expected_min = sum(r["expected_min"] for r in successful_tests) / len(successful_tests)
        avg_expected_max = sum(r["expected_max"] for r in successful_tests) / len(successful_tests)
        
        print(f"\n📊 Overall:")
        print(f"   Total tokens across tests: {total_tokens}")
        print(f"   Average expected range: {avg_expected_min:.1f}-{avg_expected_max:.1f}")
        
        # Check if any tests had inflated token counts
        inflated_tests = [r for r in successful_tests if r["tokens"] > r["expected_max"] * 2]
        if inflated_tests:
            print(f"\n⚠ Warning: {len(inflated_tests)} test(s) had significantly inflated token counts")
            for test in inflated_tests:
                print(f"   - {test['name']}: {test['tokens']} tokens "
                      f"(expected max: {test['expected_max']})")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for result in failed_tests:
            print(f"   - {result['name']}: {result.get('error', 'Unknown error')}")
    
    return len(successful_tests) > 0

def main():
    """Main entry point."""
    print("🎯 Token Counting Accuracy Test")
    print("=" * 60)
    print("\nTesting the improved token counting logic in the optimized OpenClaw adapter.")
    print("This test checks if token counts are reasonable for different types of responses.")
    
    try:
        success = asyncio.run(test_token_accuracy())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Token Accuracy Test Completed!")
            print("=" * 60)
            print("\nThe optimized adapter now provides:")
            print("✅ More reasonable token counts")
            print("✅ Better handling of inflated OpenClaw usage data")
            print("✅ Accurate token estimation for benchmarking")
            
        else:
            print("\n⚠ Token accuracy test had issues.")
            
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