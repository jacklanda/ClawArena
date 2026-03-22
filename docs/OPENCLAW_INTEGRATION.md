# OpenClaw Integration Guide

This document explains how to use ClawArena to test OpenClaw agents (lobsters 🦞) on real-world tasks.

## Overview

ClawArena now includes native support for OpenClaw agents through the `OpenClawAdapter`. This adapter allows any OpenClaw agent to be evaluated within the ClawArena benchmarking framework, providing standardized scoring and comparison capabilities.

## Prerequisites

1. **OpenClaw Installation**: Ensure OpenClaw is installed and accessible in your PATH
   ```bash
   openclaw --version
   ```

2. **ClawArena Installation**: Install ClawArena with development dependencies
   ```bash
   pip install -e ".[dev]"
   ```

3. **OpenClaw Agent Configuration**: Ensure your OpenClaw agents are properly configured and accessible

## Available OpenClaw Tasks

The framework includes specialized tasks designed for OpenClaw agent evaluation:

### 1. Email Composition (`openclaw_email_composition`)
- **Category**: Email
- **Difficulty**: Medium
- **Tests**: Professional email writing with context awareness
- **Evaluation**: Format, clarity, professionalism, completeness

### 2. Code Review (`openclaw_code_review`)
- **Category**: General
- **Difficulty**: Hard
- **Tests**: Python code analysis and improvement suggestions
- **Evaluation**: Bug identification, optimizations, code quality

### 3. Document Summarization (`openclaw_document_summarization`)
- **Category**: Summarization
- **Difficulty**: Medium
- **Tests**: Technical documentation summarization
- **Evaluation**: Content coverage, clarity, structure, conciseness

## Running OpenClaw Tests

### Basic Usage

```bash
# List available tasks (including OpenClaw tasks)
clawarena list tasks

# Run OpenClaw agent on all OpenClaw-specific tasks
clawarena run --agent openclaw --agent-id claude --category openclaw

# Run specific OpenClaw task
clawarena run --agent openclaw --agent-id gpt-4 --task openclaw_email_composition

# Run with custom workspace
clawarena run --agent openclaw --agent-id gemini --workspace-dir ./my_workspace
```

### Advanced Configuration

```bash
# Run with model override
clawarena run --agent openclaw --agent-id claude --model-override claude-3-opus

# Run with increased timeout
clawarena run --agent openclaw --agent-id gpt-4 --timeout-seconds 600

# Run multiple agents for comparison
clawarena run --agent openclaw --agent-id claude --agent openclaw --agent-id gpt-4 --agent dummy
```

### Python API Usage

```python
from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter
from clawarena.engine.runner import RunEngine
from clawarena.tasks.registry import TaskRegistry

# Create OpenClaw adapter
adapter = OpenClawAdapter(
    agent_id="claude",
    openclaw_path="openclaw",
    model_override="claude-3-sonnet",
    timeout_seconds=300,
)

# Get tasks
registry = TaskRegistry()
tasks = registry.filter(category="openclaw")

# Run evaluation
engine = RunEngine()
results = await engine.run_tasks(tasks, [adapter])

# Display results
from clawarena.reporting.leaderboard import display_leaderboard
display_leaderboard(results)
```

## Adapter Configuration Options

The `OpenClawAdapter` supports the following configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `agent_id` | str | `"claude"` | OpenClaw agent ID to use |
| `openclaw_path` | str | `"openclaw"` | Path to OpenClaw executable |
| `workspace_dir` | Optional[str] | `None` | Custom workspace directory |
| `model_override` | Optional[str] | `None` | Override default model |
| `timeout_seconds` | int | `300` | Maximum execution time per task |

## Evaluation Methodology

OpenClaw agents are evaluated using ClawArena's multi-dimensional scoring system:

### Scoring Dimensions
1. **Correctness (40%)**: Accuracy of the response relative to task requirements
2. **Completeness (25%)**: Coverage of all requested elements
3. **Efficiency (20%)**: Token usage and execution time efficiency
4. **Robustness (15%)**: Error handling and graceful degradation

### Evaluation Methods
- **Rubric-based**: Criteria-based scoring with weighted dimensions
- **LLM Judge**: AI-assisted evaluation (when available)
- **Composite**: Combined evaluation for balanced scoring

## Creating Custom OpenClaw Tasks

### Task Definition Template

```yaml
id: custom_openclaw_task
name: "Custom OpenClaw Task"
category: openclaw  # Use "openclaw" category for OpenClaw-specific tasks
difficulty: medium
execution_mode: single_turn
timeout_seconds: 300

instruction: |
  Clear task instructions here...
  
  Requirements:
  - Specific requirement 1
  - Specific requirement 2

context:
  key1: "value1"
  key2: ["list", "of", "values"]
  file_content: "Content of a file to process"

expected_output: |
  Description of expected output format and content...

evaluation:
  method: rubric
  criteria:
    - name: criterion1
      weight: 0.3
      description: "Description of what this criterion evaluates"
    - name: criterion2
      weight: 0.7
      description: "Description of what this criterion evaluates"

metadata:
  tags: ["openclaw", "custom", "your-tag"]
  created: "YYYY-MM-DD"
  author: "Your Name"
  target_agents: ["openclaw", "claude", "gpt-4", "gemini"]
```

### Best Practices for OpenClaw Tasks

1. **Clear Instructions**: Provide unambiguous task requirements
2. **Structured Context**: Use consistent context format for parsing
3. **Realistic Scenarios**: Base tasks on real-world use cases
4. **Progressive Difficulty**: Include tasks of varying complexity
5. **Comprehensive Evaluation**: Define clear evaluation criteria

## Results and Reporting

### Viewing Results

```bash
# List all results
clawarena results list

# View specific run results
clawarena results show <run_id>

# Generate leaderboard
clawarena leaderboard

# Export results
clawarena results export --format csv
clawarena results export --format json
clawarena results export --format markdown
```

### Result Interpretation

Results include:
- **Overall Score**: Weighted combination of all dimensions
- **Dimension Scores**: Individual scores for correctness, completeness, efficiency, robustness
- **Cost Analysis**: Estimated USD cost based on token usage
- **Execution Metrics**: Duration, API calls, token counts
- **Error Logs**: Any execution errors or warnings

## Troubleshooting

### Common Issues

1. **OpenClaw Not Found**
   ```
   Error: OpenClaw not found at 'openclaw'
   ```
   **Solution**: Ensure OpenClaw is installed and in your PATH

2. **Agent Execution Timeout**
   ```
   Error: OpenClaw execution timed out after 300 seconds
   ```
   **Solution**: Increase timeout with `--timeout-seconds` option

3. **Workspace Permission Issues**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   **Solution**: Ensure workspace directory is writable or use default temp directory

4. **Task Validation Errors**
   ```
   ValidationError: Invalid task definition
   ```
   **Solution**: Check YAML syntax and required fields in task definition

### Debug Mode

Enable debug logging for detailed execution information:

```bash
clawarena run --agent openclaw --agent-id claude --task openclaw_email_composition --verbose
```

## Extending the Integration

### Custom Adapters

You can create custom adapters for specific OpenClaw configurations:

```python
from clawarena.adapters.builtin.openclaw_adapter import OpenClawAdapter

class CustomOpenClawAdapter(OpenClawAdapter):
    """Custom adapter with specialized configuration."""
    
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="custom-agent",
            openclaw_path="/custom/path/openclaw",
            model_override="special-model",
            timeout_seconds=600,
            **kwargs
        )
    
    async def run_task(self, task):
        # Custom pre-processing
        modified_task = self._custom_preprocess(task)
        
        # Run with parent implementation
        response = await super().run_task(modified_task)
        
        # Custom post-processing
        return self._custom_postprocess(response)
```

### Contributing New Tasks

To contribute new OpenClaw tasks:

1. Create task definition in `tasks/openclaw/` directory
2. Follow naming convention: `openclaw_<task_name>.yaml`
3. Include comprehensive evaluation criteria
4. Test with multiple agent types
5. Submit pull request to the repository

## Roadmap

### Planned Enhancements

1. **Multi-turn Conversations**: Support for dialog-based tasks
2. **Tool Usage Testing**: Evaluation of agent tool invocation capabilities
3. **Real-time Monitoring**: Live execution monitoring and progress tracking
4. **Batch Processing**: Parallel execution of multiple tasks
5. **Advanced Analytics**: Detailed performance analytics and visualization

### Community Contributions

We welcome contributions in the following areas:
- New task definitions for OpenClaw agents
- Enhanced evaluation methodologies
- Additional adapter implementations
- Documentation improvements
- Bug fixes and performance optimizations

## Support

For issues, questions, or contributions:
- GitHub Issues: [ClawArena Repository](https://github.com/jacklanda/ClawArena)
- Documentation: [ClawArena Docs](https://github.com/jacklanda/ClawArena/docs)
- Community: [OpenClaw Discord](https://discord.com/invite/clawd)

---

*Last updated: March 22, 2024*  
*ClawArena Team*