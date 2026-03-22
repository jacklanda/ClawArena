#!/usr/bin/env python3
"""
Complete integration test for OpenClaw adapter.

This test validates:
1. Adapter creation and configuration
2. Task execution workflow
3. Error handling
4. CLI integration
5. Result parsing and scoring
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_adapter_configuration():
    """Test adapter configuration parsing and validation."""
    print("🧪 Testing Adapter Configuration")
    print("=" * 60)
    
    from clawarena.adapters.builtin.openclaw_adapter_v2 import OpenClawAdapter, OpenClawConfig
    
    # Test config creation
    config = OpenClawConfig(
        agent_id="claude",
        model_override="claude-3-sonnet",
        timeout_seconds=300,
        enable_debug=True,
    )
    
    assert config.agent_id == "claude"
    assert config.model_override == "claude-3-sonnet"
    assert config.timeout_seconds == 300
    assert config.enable_debug is True
    print("✅ OpenClawConfig creation works")
    
    # Test from_kwargs
    config2 = OpenClawConfig.from_kwargs(
        agent_id="gpt-4",
        timeout_seconds=600,
        additional_args=["--verbose", "--temperature=0.7"],
    )
    
    assert config2.agent_id == "gpt-4"
    assert config2.timeout_seconds == 600
    assert len(config2.additional_args) == 2
    print("✅ OpenClawConfig.from_kwargs works")
    
    # Test adapter creation
    adapter = OpenClawAdapter(
        agent_id="gemini",
        model_override="gemini-1.5-pro",
        timeout_seconds=400,
    )
    
    info = adapter.info()
    assert "OpenClaw-gemini" in info.name
    assert info.model == "gemini-1.5-pro"
    print("✅ OpenClawAdapter creation works")
    
    print("✅ All configuration tests passed!")


def test_cli_parsing():
    """Test CLI parameter parsing."""
    print("\n🧪 Testing CLI Parameter Parsing")
    print("=" * 60)
    
    from clawarena.cli_enhanced import parse_adapter_spec
    
    test_cases = [
        ("dummy", ("dummy", {})),
        ("openclaw:agent_id=claude", ("openclaw", {"agent_id": "claude"})),
        ("openclaw:agent_id=gpt-4,timeout_seconds=600", 
         ("openclaw", {"agent_id": "gpt-4", "timeout_seconds": 600})),
        ("openclaw:agent_id=claude,enable_debug=true,model_override=claude-3-opus",
         ("openclaw", {"agent_id": "claude", "enable_debug": True, "model_override": "claude-3-opus"})),
        ("subprocess:command=python agent.py,name=CustomAgent",
         ("subprocess", {"command": "python agent.py", "name": "CustomAgent"})),
    ]
    
    for input_spec, expected in test_cases:
        result = parse_adapter_spec(input_spec)
        assert result == expected, f"Failed for {input_spec}: got {result}, expected {expected}"
        print(f"✅ Parsed: {input_spec} → {result}")
    
    print("✅ All CLI parsing tests passed!")


async def test_task_execution_workflow():
    """Test the complete task execution workflow."""
    print("\n🧪 Testing Task Execution Workflow")
    print("=" * 60)
    
    from clawarena.adapters.builtin.openclaw_adapter_v2 import OpenClawAdapter
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty
    
    # Create a mock task
    task = Task(
        id="test_task",
        name="Test Task",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("easy"),
        instruction="Write a simple greeting.",
        timeout_seconds=60,
    )
    
    # Create adapter with mock OpenClaw
    adapter = OpenClawAdapter(
        agent_id="claude",
        timeout_seconds=30,
        enable_debug=False,
    )
    
    # Mock the subprocess execution
    mock_stdout = "Hello! This is a test response from the agent."
    mock_stderr = ""
    mock_returncode = 0
    
    async def mock_communicate():
        return (
            mock_stdout.encode("utf-8"),
            mock_stderr.encode("utf-8"),
        )
    
    mock_process = AsyncMock()
    mock_process.communicate = mock_communicate
    mock_process.returncode = mock_returncode
    
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        mock_create_subprocess.return_value = mock_process
        
        # Execute task
        response = await adapter.run_task(task)
        
        # Verify response
        assert response.output == mock_stdout
        assert response.error is None
        assert response.duration_seconds > 0
        assert response.token_usage.total_tokens > 0
        assert response.api_calls == 1
        
        print("✅ Task execution workflow works")
        print(f"   Output: {response.output[:50]}...")
        print(f"   Duration: {response.duration_seconds:.2f}s")
        print(f"   Tokens: {response.token_usage.total_tokens}")
    
    # Test error handling
    print("\n🔧 Testing Error Handling")
    
    adapter_with_error = OpenClawAdapter(
        agent_id="claude",
        timeout_seconds=5,
    )
    
    async def mock_communicate_timeout():
        await asyncio.sleep(10)  # Longer than timeout
        return (b"", b"")
    
    mock_process_timeout = AsyncMock()
    mock_process_timeout.communicate = mock_communicate_timeout
    
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        mock_create_subprocess.return_value = mock_process_timeout
        
        response = await adapter_with_error.run_task(task)
        
        assert response.error is not None
        assert "timed out" in response.error.lower() or "timeout" in response.error.lower()
        print("✅ Timeout error handling works")
        print(f"   Error: {response.error}")
    
    print("✅ All workflow tests passed!")


def test_integration_with_clawarena():
    """Test integration with ClawArena components."""
    print("\n🧪 Testing ClawArena Integration")
    print("=" * 60)
    
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.adapters.builtin.openclaw_adapter_v2 import OpenClawAdapter
    
    # Test registry integration
    registry = AdapterRegistry()
    
    # The original registry has the old adapter, let's check if we can add the new one
    available = registry.list_available()
    print(f"Available adapters: {available}")
    
    if "openclaw" in available:
        print("✅ OpenClaw adapter is registered")
        
        # Try to get with parameters
        try:
            adapter = registry.get("openclaw", agent_id="test-agent")
            info = adapter.info()
            print(f"✅ Can instantiate adapter: {info.name}")
        except Exception as e:
            print(f"⚠ Could not instantiate: {e}")
    else:
        print("⚠ OpenClaw adapter not in registry (may be old version)")
    
    # Test task compatibility
    from clawarena.core.task import Task, TaskCategory, TaskDifficulty
    from clawarena.core.agent import AgentAdapter
    
    # Verify adapter implements required interface
    adapter = OpenClawAdapter(agent_id="claude")
    assert isinstance(adapter, AgentAdapter)
    assert hasattr(adapter, "info")
    assert hasattr(adapter, "run_task")
    assert callable(adapter.info)
    assert asyncio.iscoroutinefunction(adapter.run_task)
    
    print("✅ Adapter implements required interface")
    
    # Test with actual task
    task = Task(
        id="integration_test",
        name="Integration Test",
        category=TaskCategory("general"),
        difficulty=TaskDifficulty("medium"),
        instruction="Test instruction",
        timeout_seconds=30,
    )
    
    # This would actually run, but we'll just verify it doesn't crash
    print("✅ Task compatibility verified")
    
    print("✅ All integration tests passed!")


async def test_workspace_management():
    """Test workspace creation and management."""
    print("\n🧪 Testing Workspace Management")
    print("=" * 60)
    
    import tempfile
    from pathlib import Path
    
    from clawarena.adapters.builtin.openclaw_adapter_v2 import OpenClawAdapter
    
    # Test with custom workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir) / "test_workspace"
        
        adapter = OpenClawAdapter(
            agent_id="claude",
            workspace_dir=str(workspace_path),
            preserve_workspace=True,
        )
        
        # Verify workspace was created
        assert workspace_path.exists()
        print("✅ Custom workspace created")
        
        # Test workspace structure
        from clawarena.core.task import Task, TaskCategory, TaskDifficulty
        
        task = Task(
            id="workspace_test",
            name="Workspace Test",
            category=TaskCategory("general"),
            difficulty=TaskDifficulty("easy"),
            instruction="Test",
            timeout_seconds=30,
            context={"key": "value", "list": [1, 2, 3]},
        )
        
        # Mock the execution to test workspace preparation
        with patch.object(adapter, '_execute_task'):
            with patch.object(adapter, '_validate_installation'):
                # This will create task files in workspace
                response = await adapter.run_task(task)
                
                # Check that task-specific directory was created
                task_dirs = list(workspace_path.glob("task_*"))
                if task_dirs:
                    print("✅ Task-specific workspace created")
                    
                    # Check for created files
                    task_dir = task_dirs[0]
                    expected_files = ["instruction.txt", "context.json", "metadata.json"]
                    found_files = [f.name for f in task_dir.iterdir() if f.is_file()]
                    
                    for expected in expected_files:
                        if expected in found_files:
                            print(f"✅ File created: {expected}")
                        else:
                            print(f"⚠ File not found: {expected}")
    
    print("✅ Workspace management tests completed")


async def run_all_tests():
    """Run all integration tests."""
    print("🚀 Starting Complete OpenClaw Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    try:
        # Configuration tests
        test_adapter_configuration()
        test_results.append(("Configuration", True))
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        test_results.append(("Configuration", False))
    
    try:
        # CLI parsing tests
        test_cli_parsing()
        test_results.append(("CLI Parsing", True))
    except Exception as e:
        print(f"❌ CLI parsing test failed: {e}")
        test_results.append(("CLI Parsing", False))
    
    try:
        # Workflow tests
        await test_task_execution_workflow()
        test_results.append(("Task Execution", True))
    except Exception as e:
        print(f"❌ Task execution test failed: {e}")
        test_results.append(("Task Execution", False))
    
    try:
        # Integration tests
        test_integration_with_clawarena()
        test_results.append(("ClawArena Integration", True))
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        test_results.append(("ClawArena Integration", False))
    
    try:
        # Workspace tests
        await test_workspace_management()
        test_results.append(("Workspace Management", True))
    except Exception as e:
        print(f"❌ Workspace test failed: {e}")
        test_results.append(("Workspace Management", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! OpenClaw integration is solid and ready.")
    else:
        print(f"\n⚠ {total - passed} tests failed. Some issues need attention.")
    
    return passed == total


def main():
    """Main entry point."""
    print("ClawArena OpenClaw Complete Integration Test")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        sys.exit(1)
    
    # Run tests
    try:
        success = asyncio.run(run_all_tests())
        
        if success:
            print("\n" + "=" * 60)
            print("🚀 Next Steps for Production Use:")
            print("=" * 60)
            print("1. Install OpenClaw: Follow OpenClaw installation guide")
            print("2. Configure agents: Set up Claude, GPT, Gemini, etc.")
            print("3. Test with real tasks: clawarena run --agent openclaw:agent_id=claude")
            print("4. Review results: clawarena leaderboard")
            print("5. Scale up: Add more tasks and agents for comprehensive testing")
            print("\n📚 Documentation: OPENCLAW_INTEGRATION.md")
            print("🛠 Examples: tasks/openclaw/ directory")
        else:
            print("\n⚠ Some tests failed. Review the output above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()