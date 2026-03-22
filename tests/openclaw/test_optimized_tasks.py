#!/usr/bin/env python3
"""
Test optimized OpenClaw adapter on email and summarization tasks.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_email_task():
    """Test email composition task with optimized adapter."""
    print("📧 Testing Email Composition Task (Optimized)")
    print("=" * 60)
    
    from clawarena.adapters.registry_optimized import optimized_registry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create email task (similar to the built-in one)
    email_task = Task(
        id="email_compose_professional",
        name="Compose Professional Email",
        category=TaskCategory("email"),
        difficulty=TaskDifficulty("medium"),
        description="Compose a professional email with given context",
        instruction="""
        Write a professional email using the information provided in the context.
        The email should:
        1. Use an appropriate greeting for the recipient.
        2. Clearly convey all the key points listed below.
        3. Maintain a polite and professional tone throughout.
        4. End with a professional sign-off using the sender's name.
        5. Be concise — no more than 200 words in the body.
        
        Context:
        - Sender: Jordan Rivera (Product Manager)
        - Recipient: Alex Chen (alex.chen@acmecorp.com)
        - Relationship: colleague on the same team
        - Subject: Q3 Feature Prioritization Meeting
        - Key points:
          1. Propose scheduling a meeting next Tuesday at 2 PM to review Q3 feature priorities
          2. Ask Alex to prepare the latest customer feedback summary before the meeting
          3. Mention that the VP of Product wants the finalized list by end of week
          4. Offer to share the draft roadmap document ahead of time
        """,
        evaluation=EvaluationSpec(evaluator="rubric", config={
            "criteria": [
                {"name": "greeting", "description": "Appropriate professional greeting", "weight": 1},
                {"name": "key_points", "description": "All key points addressed", "weight": 3},
                {"name": "tone", "description": "Professional and polite tone", "weight": 2},
                {"name": "sign_off", "description": "Professional sign-off with name", "weight": 1},
                {"name": "conciseness", "description": "Concise email body", "weight": 1},
            ]
        }),
        timeout_seconds=120,
    )
    
    # Create optimized adapter
    adapter = optimized_registry.get(
        "openclaw-optimized",
        agent_id="main",
        enable_debug=False,
        timeout_seconds=60,
    )
    
    print(f"🔧 Using adapter: {adapter.info().name}")
    print(f"\n📝 Task: {email_task.name}")
    print(f"   Category: {email_task.category.value}")
    print(f"   Difficulty: {email_task.difficulty.value}")
    
    # Execute
    print(f"\n🚀 Executing email task...")
    
    try:
        response = await adapter.run_task(email_task)
        
        print(f"\n✅ Email task completed!")
        print(f"   Duration: {response.duration_seconds:.2f}s")
        print(f"   Tokens: {response.token_usage.total_tokens}")
        print(f"   Input tokens: {response.token_usage.input_tokens}")
        print(f"   Output tokens: {response.token_usage.output_tokens}")
        
        if response.error:
            print(f"❌ Error: {response.error}")
            return None
        
        # Calculate estimated cost (using approximate rates)
        # Assuming $0.50 per 1M tokens for input, $1.50 per 1M tokens for output
        input_cost = (response.token_usage.input_tokens / 1_000_000) * 0.50
        output_cost = (response.token_usage.output_tokens / 1_000_000) * 1.50
        total_cost = input_cost + output_cost
        
        print(f"   Estimated cost: ${total_cost:.6f}")
        
        # Show response
        print(f"\n📧 Generated Email ({len(response.output)} chars):")
        print("-" * 60)
        print(response.output[:800] + ("..." if len(response.output) > 800 else ""))
        print("-" * 60)
        
        # Analyze email quality
        print(f"\n🔍 Email Analysis:")
        
        # Check for key elements
        key_elements = {
            "Subject line": "subject" in response.output.lower() or "Q3" in response.output,
            "Recipient address": "alex.chen@acmecorp.com" in response.output or "Alex" in response.output,
            "Sender signature": "Jordan" in response.output or "Rivera" in response.output,
            "Meeting proposal": any(word in response.output.lower() for word in ["meeting", "tuesday", "2 pm", "schedule"]),
            "Key points covered": sum(1 for point in [
                "customer feedback", "summary", "VP", "product", "roadmap", "document"
            ] if point in response.output.lower()) >= 3,
            "Professional tone": any(word in response.output.lower() for word in ["dear", "hi", "hello", "regards", "sincerely"]),
        }
        
        for element, found in key_elements.items():
            print(f"   {'✅' if found else '❌'} {element}")
        
        # Word count
        words = len(response.output.split())
        print(f"   📊 Word count: {words} {'(within limit)' if words <= 200 else '(exceeds 200 word limit)'}")
        
        return {
            "task": "email_composition",
            "duration": response.duration_seconds,
            "tokens": response.token_usage.total_tokens,
            "input_tokens": response.token_usage.input_tokens,
            "output_tokens": response.token_usage.output_tokens,
            "cost": total_cost,
            "word_count": words,
            "quality_score": sum(1 for found in key_elements.values() if found) / len(key_elements),
            "response": response.output,
        }
        
    except Exception as e:
        print(f"❌ Email task failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await adapter.teardown()

async def test_summarization_task():
    """Test summarization task with optimized adapter."""
    print("\n" + "=" * 60)
    print("📋 Testing Summarization Task (Optimized)")
    print("=" * 60)
    
    from clawarena.adapters.registry_optimized import optimized_registry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create summarization task
    summarization_task = Task(
        id="meeting_summary",
        name="Meeting Transcript Summary",
        category=TaskCategory("summarization"),
        difficulty=TaskDifficulty("medium"),
        description="Summarize a meeting transcript",
        instruction="""
        Summarize the following meeting transcript. Your summary should:
        1. Identify the main topics discussed
        2. Extract key decisions made
        3. List action items with responsible persons
        4. Highlight any important deadlines
        5. Keep the summary concise (150-200 words)
        
        Meeting Transcript:
        Date: 2025-03-17
        Title: Weekly Product Sync
        Attendees: Sarah Kim (Product Lead), Raj Patel (Engineering Manager), Tanya Osei (Design Lead), Chris Novak (Data Analyst)
        
        Discussion:
        - Sarah opened the meeting by reviewing Q2 performance metrics. Revenue grew 15% YoY, but user retention dropped 5%.
        - Raj reported that the onboarding redesign is 80% complete. Engineering team needs 2 more weeks for testing.
        - Tanya presented new mockups for the dashboard redesign. Team agreed to proceed with Option B.
        - Chris shared data showing that feature X has the highest user engagement but also the most support tickets.
        - Key decisions:
          1. Delay onboarding launch by 1 week to allow for thorough testing.
          2. Approve dashboard redesign (Option B) for development.
          3. Create a task force to address issues with feature X.
        - Action items:
          1. Raj: Finalize onboarding testing plan by Friday.
          2. Tanya: Deliver final design assets for dashboard by Wednesday.
          3. Chris: Prepare detailed analysis of feature X issues for next meeting.
          4. Sarah: Schedule follow-up with VP of Product to discuss retention strategy.
        - Next meeting: Same time next week.
        """,
        evaluation=EvaluationSpec(evaluator="rubric", config={
            "criteria": [
                {"name": "completeness", "description": "Covers all main topics", "weight": 3},
                {"name": "clarity", "description": "Clear and organized summary", "weight": 2},
                {"name": "conciseness", "description": "Appropriate length (150-200 words)", "weight": 2},
                {"name": "action_items", "description": "Clearly lists action items", "weight": 2},
                {"name": "decisions", "description": "Highlights key decisions", "weight": 1},
            ]
        }),
        timeout_seconds=120,
    )
    
    # Create optimized adapter
    adapter = optimized_registry.get(
        "openclaw-optimized",
        agent_id="main",
        enable_debug=False,
        timeout_seconds=60,
    )
    
    print(f"🔧 Using adapter: {adapter.info().name}")
    print(f"\n📝 Task: {summarization_task.name}")
    print(f"   Category: {summarization_task.category.value}")
    print(f"   Difficulty: {summarization_task.difficulty.value}")
    
    # Execute
    print(f"\n🚀 Executing summarization task...")
    
    try:
        response = await adapter.run_task(summarization_task)
        
        print(f"\n✅ Summarization task completed!")
        print(f"   Duration: {response.duration_seconds:.2f}s")
        print(f"   Tokens: {response.token_usage.total_tokens}")
        print(f"   Input tokens: {response.token_usage.input_tokens}")
        print(f"   Output tokens: {response.token_usage.output_tokens}")
        
        if response.error:
            print(f"❌ Error: {response.error}")
            return None
        
        # Calculate estimated cost
        input_cost = (response.token_usage.input_tokens / 1_000_000) * 0.50
        output_cost = (response.token_usage.output_tokens / 1_000_000) * 1.50
        total_cost = input_cost + output_cost
        
        print(f"   Estimated cost: ${total_cost:.6f}")
        
        # Show response
        print(f"\n📋 Generated Summary ({len(response.output)} chars):")
        print("-" * 60)
        print(response.output[:1000] + ("..." if len(response.output) > 1000 else ""))
        print("-" * 60)
        
        # Analyze summary quality
        print(f"\n🔍 Summary Analysis:")
        
        # Check for key elements
        key_elements = {
            "Main topics identified": any(word in response.output.lower() for word in ["topic", "discuss", "review", "metric"]),
            "Key decisions listed": any(word in response.output.lower() for word in ["decision", "approve", "delay", "agree"]),
            "Action items extracted": any(word in response.output.lower() for word in ["action", "task", "responsible", "by"]),
            "Deadlines mentioned": any(word in response.output.lower() for word in ["friday", "wednesday", "week", "deadline"]),
            "Concise structure": len(response.output.split()) <= 250,  # Allow some flexibility
            "Clear organization": any(word in response.output.lower() for word in ["summary", "key", "action", "decision", "next"]),
        }
        
        for element, found in key_elements.items():
            print(f"   {'✅' if found else '❌'} {element}")
        
        # Word count
        words = len(response.output.split())
        print(f"   📊 Word count: {words} {'(good length)' if 150 <= words <= 250 else '(outside target range 150-200)'}")
        
        return {
            "task": "summarization",
            "duration": response.duration_seconds,
            "tokens": response.token_usage.total_tokens,
            "input_tokens": response.token_usage.input_tokens,
            "output_tokens": response.token_usage.output_tokens,
            "cost": total_cost,
            "word_count": words,
            "quality_score": sum(1 for found in key_elements.values() if found) / len(key_elements),
            "response": response.output,
        }
        
    except Exception as e:
        print(f"❌ Summarization task failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await adapter.teardown()

async def compare_with_dummy():
    """Compare optimized OpenClaw with Dummy adapter."""
    print("\n" + "=" * 60)
    print("📊 Comparing Optimized OpenClaw vs Dummy Adapter")
    print("=" * 60)
    
    from clawarena.adapters.registry_optimized import optimized_registry
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec
    
    # Create a simple comparison task
    comparison_task = Task(
        id="comparison_simple",
        name="Simple Comparison Task",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        description="Simple task for adapter comparison",
        instruction="Explain the concept of machine learning in 2-3 sentences.",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        timeout_seconds=60,
    )
    
    # Test both adapters
    adapters = [
        ("Dummy", "dummy"),
        ("OpenClaw-optimized", "openclaw-optimized"),
    ]
    
    results = {}
    
    for adapter_name, adapter_key in adapters:
        print(f"\n🔧 Testing {adapter_name} adapter...")
        
        try:
            if adapter_key == "dummy":
                registry = AdapterRegistry()
                adapter = registry.get(adapter_key)
            else:
                adapter = optimized_registry.get(
                    adapter_key,
                    agent_id="main",
                    enable_debug=False,
                    timeout_seconds=30,
                )
            
            response = await adapter.run_task(comparison_task)
            
            results[adapter_name] = {
                "success": not response.error,
                "duration": response.duration_seconds,
                "tokens": response.token_usage.total_tokens,
                "cost": 0.0,  # Dummy has no cost
                "response_preview": response.output[:150] + ("..." if len(response.output) > 150 else ""),
                "response_length": len(response.output),
                "error": response.error,
            }
            
            print(f"   ✅ Duration: {response.duration_seconds:.2f}s")
            print(f"   ✅ Tokens: {response.token_usage.total_tokens}")
            print(f"   ✅ Response: {len(response.output)} chars")
            
            if response.error:
                print(f"   ❌ Error: {response.error[:100]}...")
            
            # Clean up
            if hasattr(adapter, 'teardown'):
                await adapter.teardown()
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results[adapter_name] = {"error": str(e)}
    
    # Print comparison
    print("\n" + "=" * 60)
    print("📈 Adapter Comparison Results")
    print("=" * 60)
    
    if "Dummy" in results and "OpenClaw-optimized" in results:
        dummy = results["Dummy"]
        openclaw = results["OpenClaw-optimized"]
        
        print(f"\n📊 Performance Comparison:")
        print(f"   Duration: {dummy.get('duration', 0):.2f}s vs {openclaw.get('duration', 0):.2f}s")
        print(f"   Tokens: {dummy.get('tokens', 0)} vs {openclaw.get('tokens', 0)}")
        print(f"   Response length: {dummy.get('response_length', 0)} chars vs {openclaw.get('response_length', 0)} chars")
        
        print(f"\n🔍 Response Quality:")
        print(f"   Dummy: {dummy.get('response_preview', 'N/A')}")
        print(f"   OpenClaw: {openclaw.get('response_preview', 'N/A')}")
        
        # Quality assessment
        dummy_text = dummy.get('response_preview', '').lower()
        openclaw_text = openclaw.get('response_preview', '').lower()
        
        ml_keywords = ["machine learning", "algorithm", "data", "pattern", "predict", "learn"]
        
        dummy_has_ml = any(keyword in dummy_text for keyword in ml_keywords)
        openclaw_has_ml = any(keyword in openclaw_text for keyword in ml_keywords)
        
        print(f"\n🎯 Task Understanding:")
        print(f"   Dummy understands ML concept: {'✅' if dummy_has_ml else '❌'}")
        print(f"   OpenClaw understands ML concept: {'✅' if openclaw_has_ml else '❌'}")
    
    return results

def main():
    """Main entry point."""
    print("🎯 Optimized OpenClaw Adapter - Real Task Testing")
    print("=" * 60)
    print("\nTesting the optimized adapter on real-world tasks:")
    print("1. 📧 Email Composition Task")
    print("2. 📋 Meeting Summarization Task")
    print("3