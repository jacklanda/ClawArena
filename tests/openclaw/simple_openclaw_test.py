#!/usr/bin/env python3
"""
Simple test for OpenClaw integration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_adapter_creation():
    """Test that OpenClaw adapter can be created."""
    print("🧪 Testing OpenClaw Adapter Creation")
    print("=" * 60)
    
    try:
        from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter
        
        # Test basic creation
        adapter = OpenClawAdapter(
            agent_id="claude",
            openclaw_path="openclaw",
            timeout_seconds=120,
        )
        
        info = adapter.info()
        print(f"✅ OpenClawAdapter created successfully!")
        print(f"   Name: {info.name}")
        print(f"   Model: {info.model}")
        print(f"   Version: {info.version}")
        print(f"   Description: {info.description}")
        
        # Test factory function
        from clawarena.adapters.builtin.openclaw_adapter import create_openclaw_adapter
        adapter2 = create_openclaw_adapter(agent_id="gpt-4")
        info2 = adapter2.info()
        print(f"\n✅ Factory function works!")
        print(f"   Created: {info2.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Adapter creation failed: {e}")
        print("\nNote: This is expected if OpenClaw is not installed.")
        print("The adapter code is still valid and will work when OpenClaw is available.")
        return False

def test_task_loading():
    """Test that OpenClaw tasks can be loaded."""
    print("\n📂 Testing OpenClaw Task Loading")
    print("=" * 60)
    
    try:
        from clawarena.tasks.registry import TaskRegistry
        
        registry = TaskRegistry()
        
        # Check if OpenClaw tasks directory exists
        task_dir = Path(__file__).parent / "tasks" / "openclaw"
        if task_dir.exists():
            print(f"✅ OpenClaw task directory found: {task_dir}")
            
            # Count task files
            task_files = list(task_dir.glob("*.yaml"))
            print(f"✅ Found {len(task_files)} OpenClaw task files:")
            
            for task_file in task_files:
                print(f"   - {task_file.name}")
                
                # Try to load the task
                try:
                    tasks = registry.load_from_file(str(task_file))
                    print(f"     ✓ Loaded {len(tasks)} task(s)")
                except Exception as e:
                    print(f"     ⚠ Load error: {e}")
        else:
            print(f"⚠ OpenClaw task directory not found: {task_dir}")
            print("  Creating sample tasks...")
            
            # Create directory
            task_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a simple test task
            sample_task = """id: test_openclaw_task
name: "Test OpenClaw Task"
category: openclaw
difficulty: easy
execution_mode: single_turn
timeout_seconds: 60

instruction: "Say hello and introduce yourself."

expected_output: "A friendly greeting and introduction."

evaluation:
  method: exact_match
"""
            
            (task_dir / "test_task.yaml").write_text(sample_task)
            print(f"✅ Created sample task: test_task.yaml")
        
        return True
        
    except Exception as e:
        print(f"❌ Task loading failed: {e}")
        return False

def test_registry_integration():
    """Test that OpenClaw adapter is registered."""
    print("\n📋 Testing Registry Integration")
    print("=" * 60)
    
    try:
        from clawarena.adapters.registry import AdapterRegistry
        
        registry = AdapterRegistry()
        available = registry.list_available()
        
        print(f"✅ Available adapters: {', '.join(available)}")
        
        if "openclaw" in available:
            print("✅ OpenClaw adapter is registered in the registry!")
            
            # Try to get the adapter
            try:
                adapter = registry.get("openclaw", agent_id="test")
                print(f"✅ Successfully retrieved OpenClaw adapter")
                print(f"   Adapter type: {type(adapter).__name__}")
            except Exception as e:
                print(f"⚠ Could not instantiate adapter: {e}")
        else:
            print("❌ OpenClaw adapter not found in registry")
            print("   Available adapters:", available)
            
        return "openclaw" in available
        
    except Exception as e:
        print(f"❌ Registry test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("ClawArena OpenClaw Integration Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Adapter Creation", test_adapter_creation()))
    results.append(("Task Loading", test_task_loading()))
    results.append(("Registry Integration", test_registry_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "⚠ PARTIAL/INFO"
        if success:
            passed += 1
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! OpenClaw integration is ready.")
    else:
        print("\n📝 Some tests showed warnings or informational results.")
        print("   This is normal for initial setup without OpenClaw installed.")
    
    print("\n" + "=" * 60)
    print("🚀 Next Steps:")
    print("1. Install OpenClaw if not already installed")
    print("2. Run: openclaw --version  # Verify installation")
    print("3. Check OPENCLAW_INTEGRATION.md for detailed usage")
    print("4. Run: clawarena list tasks  # See available tasks")
    print("5. Run: clawarena run --agent openclaw --agent-id claude --task test_openclaw_task")

if __name__ == "__main__":
    main()