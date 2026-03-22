#!/usr/bin/env python3
"""
Test script for OpenClaw integration with ClawArena.

This script demonstrates how to use the OpenClawAdapter to test
OpenClaw agents on real-world tasks and display the results.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter
from clawarena.adapters.builtin.dummy import DummyAdapter
from clawarena.engine.runner import RunEngine
from clawarena.tasks.registry import TaskRegistry
from clawarena.reporting.table import display_results_table
from clawarena.core.scoring import Leaderboard


async def test_openclaw_adapter():
    """Test the OpenClaw adapter with sample tasks."""
    
    print("🧪 Testing OpenClaw Integration with ClawArena")
    print("=" * 60)
    
    # Create adapters
    adapters = []
    
    # Dummy adapter for baseline comparison
    dummy_adapter = DummyAdapter()
    adapters.append(dummy_adapter)
    print(f"✓ Created DummyAdapter: {dummy_adapter.info().name}")
    
    # OpenClaw adapter (commented out by default - uncomment to test with real OpenClaw)
    try:
        openclaw_adapter = OpenClawAdapter(
            agent_id="claude",
            openclaw_path="openclaw",
            timeout_seconds=120,  # Shorter timeout for testing
        )
        adapters.append(openclaw_adapter)
        print(f"✓ Created OpenClawAdapter: {openclaw_adapter.info().name}")
    except Exception as e:
        print(f"⚠ OpenClawAdapter creation failed: {e}")
        print("  (This is expected if OpenClaw is not installed)")
        print("  Using DummyAdapter only for demonstration...")
    
    # Get tasks
    registry = TaskRegistry()
    
    # Load OpenClaw-specific tasks
    openclaw_tasks = []
    task_dir = Path(__file__).parent / "tasks" / "openclaw"
    
    if task_dir.exists():
        for task_file in task_dir.glob("*.yaml"):
            try:
                tasks = registry.load_from_file(str(task_file))
                openclaw_tasks.extend(tasks)
                print(f"✓ Loaded task from: {task_file.name}")
            except Exception as e:
                print(f"⚠ Failed to load task {task_file}: {e}")
    
    if not openclaw_tasks:
        # Fallback to any available tasks
        print("⚠ No OpenClaw tasks found, using all available tasks")
        openclaw_tasks = list(registry.all_tasks())
    
    # Limit to 2 tasks for quick testing
    test_tasks = openclaw_tasks[:2]
    
    if not test_tasks:
        print("❌ No tasks available for testing")
        return
    
    print(f"✓ Selected {len(test_tasks)} tasks for testing")
    for task in test_tasks:
        print(f"  - {task.name} ({task.category.value}, {task.difficulty.value})")
    
    # Run tasks
    print("\n🚀 Running tasks...")
    engine = RunEngine()
    
    try:
        results = await engine.run_tasks(test_tasks, adapters)
        
        print("\n📊 Results Summary")
        print("=" * 60)
        
        # Display run results
        print("\n📊 Run Results:")
        for result in results:
            print(f"\nTask: {result.task.name}")
            print(f"Agent: {result.agent_info.name}")
            print(f"Score: {result.score:.2f}/100")
            print(f"Duration: {result.duration_seconds:.2f}s")
        
        print("\n🏆 Leaderboard")
        print("=" * 60)
        
        # Create and display leaderboard
        leaderboard = Leaderboard.from_runs(results)
        print(f"\nTop Agents:")
        for entry in leaderboard.entries[:5]:  # Show top 5
            print(f"  {entry.rank}. {entry.agent_name}: {entry.score:.2f}")
        
        # Print detailed metrics
        print("\n📈 Detailed Metrics")
        print("=" * 60)
        
        for result in results:
            print(f"\nTask: {result.task.name}")
            print(f"Agent: {result.agent_info.name}")
            print(f"Score: {result.score:.2f}/100")
            print(f"Duration: {result.duration_seconds:.2f}s")
            print(f"Tokens: {result.token_usage.total_tokens}")
            print(f"Cost: ${result.cost_estimate:.4f}")
            
            if result.error:
                print(f"Error: {result.error}")
            
            # Print dimension scores
            if hasattr(result, 'dimension_scores'):
                print("Dimension Scores:")
                for dim, score in result.dimension_scores.items():
                    print(f"  {dim}: {score:.2f}")
        
        print("\n✅ OpenClaw integration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


async def demo_openclaw_capabilities():
    """Demonstrate OpenClaw adapter capabilities."""
    
    print("\n" + "=" * 60)
    print("🦞 OpenClaw Adapter Capabilities Demo")
    print("=" * 60)
    
    # Create adapter with various configurations
    configs = [
        {
            "name": "Claude Agent",
            "agent_id": "claude",
            "model_override": "claude-3-sonnet",
        },
        {
            "name": "GPT Agent",
            "agent_id": "gpt-4",
            "model_override": "gpt-4-turbo",
        },
        {
            "name": "Gemini Agent",
            "agent_id": "gemini",
            "model_override": "gemini-1.5-pro",
        },
        {
            "name": "Custom Workspace",
            "agent_id": "claude",
            "workspace_dir": "./test_workspace",
            "timeout_seconds": 600,
        },
    ]
    
    for config in configs:
        try:
            adapter = OpenClawAdapter(**{k: v for k, v in config.items() if k != 'name'})
            info = adapter.info()
            
            print(f"\n🔧 {config['name']}:")
            print(f"   Name: {info.name}")
            print(f"   Model: {info.model}")
            print(f"   Version: {info.version}")
            print(f"   Metadata: {info.metadata}")
            
        except Exception as e:
            print(f"\n⚠ {config['name']} configuration failed: {e}")
    
    print("\n📋 Available Configuration Options:")
    print("   - agent_id: OpenClaw agent identifier")
    print("   - openclaw_path: Path to OpenClaw executable")
    print("   - workspace_dir: Custom workspace directory")
    print("   - model_override: Model specification override")
    print("   - timeout_seconds: Maximum execution time")
    print("   - **kwargs: Additional adapter-specific options")


def main():
    """Main entry point."""
    
    print("ClawArena OpenClaw Integration Test")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        sys.exit(1)
    
    # Run tests
    try:
        asyncio.run(test_openclaw_adapter())
        asyncio.run(demo_openclaw_capabilities())
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("\nNext steps:")
        print("1. Install OpenClaw if not already installed")
        print("2. Configure your OpenClaw agents")
        print("3. Run: python test_openclaw_integration.py")
        print("4. Check OPENCLAW_INTEGRATION.md for detailed usage")
        
    except KeyboardInterrupt:
        print("\n\n⏹ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()