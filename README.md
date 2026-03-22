# ClawArena

An agent benchmarking arena for evaluating AI agent systems on real-world tasks.

## Overview

ClawArena is a Python framework for running AI agents against standardized task suites, evaluating their performance across multiple dimensions, and generating comparative leaderboards. It provides a plugin-based architecture that makes it easy to integrate custom agents, evaluators, and task definitions.

## Implemented Features

### Core Framework

- **Task Model** -- Structured task definitions with category, difficulty, execution mode, evaluation spec, context, expected output, and timeout
- **Agent Adapter Interface** -- Abstract base class for plugging in any agent system, with lifecycle hooks and structured response tracking (tokens, duration, API calls, traces)
- **Multi-Dimensional Scoring** -- Responses evaluated on correctness (40%), completeness (25%), efficiency (20%), and robustness (15%) with configurable weights
- **Cost Estimation** -- Automatic USD cost calculation from token usage, with built-in pricing for Anthropic, OpenAI, Google, and Meta models
- **Leaderboard Generation** -- Ranked agent comparison sorted by score, cost, or speed

### Task System

- **YAML Task Definitions** -- Declarative task specs validated with Pydantic
- **Task Registry** -- Central discovery with filtering by category and difficulty
- **10 Built-in Tasks** across four categories:
  - **Email** -- compose_simple, reply_with_context, thread_summary_reply
  - **Summarization** -- meeting_notes, daily_standup, multi_source
  - **Cascade** -- extract_and_email, data_pipeline
  - **General** -- file_organizer, schedule_planner

### Evaluators

- **Exact Match** -- String comparison with sequence matching, contains-list checking, and email format validation
- **Rubric** -- Criterion-based scoring with keyword/phrase detection heuristics
- **LLM Judge** -- Uses OpenAI or Anthropic APIs to score responses, with graceful fallback to heuristic scoring
- **Composite** -- Combines multiple evaluators into a single pipeline

### Agent Adapters

- **Dummy Adapter** -- Returns canned responses for framework testing
- **Subprocess Adapter** -- Runs external agents as subprocesses with command templates (`{instruction}`, `{context_file}`, `{task_id}`)
- **Plugin Discovery** -- Third-party adapters discovered via Python entry points

### Execution Engine

- **Run Engine** -- Orchestrates task execution against one or more adapters
- **Sandboxing** -- Each task runs in an isolated temp directory with fixture provisioning
- **Async-First** -- All agent execution and evaluation is fully async

### Storage & Reporting

- **JSON File Store** -- Persists run results as JSON with an index for quick lookups
- **Rich Terminal Output** -- Formatted tables for run results and leaderboards via Rich
- **Multiple Export Formats** -- Table, CSV, JSON, and Markdown

### CLI

```
clawarena run          # Execute tasks against agents
clawarena list         # Show available tasks, agents, or evaluators
clawarena results      # View and compare run results
clawarena leaderboard  # Display ranked agent results
clawarena validate     # Validate task YAML files
```

Supports task filtering by category, difficulty, or ID; timeout overrides; custom task directories; and output directory configuration.

## Installation

```bash
# Core install
pip install -e .

# With LLM judge support
pip install -e ".[llm]"

# With dev tools
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Quick Start

```bash
# List available tasks
clawarena list tasks

# Run the dummy adapter against all tasks
clawarena run --agent dummy

# Run against a specific category
clawarena run --agent dummy --category email

# View results
clawarena results list
clawarena leaderboard
```

## Project Structure

```
src/clawarena/
  core/           # Data models -- Task, AgentAdapter, Evaluator, Result, Scoring
  tasks/          # YAML loader, registry, and 10 built-in task definitions
  evaluators/     # Exact match, rubric, LLM judge, and composite evaluators
  adapters/       # Adapter registry, dummy, and subprocess adapters
  engine/         # Run engine, pricing table, and sandbox isolation
  storage/        # Abstract backend and JSON file store
  reporting/      # Rich table rendering and leaderboard display
  cli.py          # Click-based CLI entry point
tests/            # Unit tests across all modules
tasks/examples/   # Example task YAML for reference
```

## Roadmap

### v0.2.0 -- Agent Ecosystem

- [ ] Built-in adapters for Claude, GPT, and Gemini agents
- [ ] Multi-turn conversation task support
- [ ] Agent memory and tool-use tracking across turns
- [ ] Streaming response capture

### v0.3.0 -- Evaluation & Observability

- [ ] Custom evaluator plugin discovery via entry points
- [ ] Evaluation explanations and per-criterion breakdowns in results
- [ ] OpenTelemetry tracing integration for full run observability
- [ ] Side-by-side diff view for comparing agent outputs

### v0.4.0 -- Scalability & Parallelism

- [ ] Parallel task execution across agents
- [ ] Distributed runner support (task queue backend)
- [ ] Rate limiting and retry policies per adapter
- [ ] Result caching to avoid redundant runs

### v0.5.0 -- Richer Task Library

- [ ] Code generation and debugging task categories
- [ ] Multi-step agentic workflow tasks (tool use, web browsing, file editing)
- [ ] Community task contribution format and validation pipeline
- [ ] Task difficulty auto-calibration from historical pass rates

### v1.0.0 -- Production Release

- [ ] Web dashboard for interactive leaderboard exploration
- [ ] Database storage backend (SQLite / PostgreSQL)
- [ ] CI integration helpers (GitHub Actions, etc.)
- [ ] Stable public API with semantic versioning guarantees
- [ ] Comprehensive documentation site

## License

Apache 2.0
