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

### OpenClaw Integration 🦞

- **OpenClaw Agent Adapter** -- Native support for testing OpenClaw agents (lobsters) on real-world tasks
- **Specialized Task Suite** -- Pre-defined tasks optimized for OpenClaw agent evaluation
- **Sandboxed Execution** -- Isolated task execution with proper workspace management
- **Comprehensive Metrics** -- Detailed performance analytics for OpenClaw agents

### Task System

- **YAML Task Definitions** -- Declarative task specs validated with Pydantic
- **Task Registry** -- Central discovery with filtering by category and difficulty
- **35 Built-in Tasks** across five categories:

| # | ID | Name | Category | Difficulty | Timeout | Mode |
|---|---|---|---|---|---|---|
| 1 | `cascade.data_pipeline` | Log Analysis to Incident Report Pipeline | cascade | hard | 360s | sandboxed |
| 2 | `cascade.extract_and_email` | Extract Metrics, Summarize, and Compose Email | cascade | medium | 240s | sandboxed |
| 3 | `email.compose_simple` | Compose a Professional Email | email | easy | 120s | sandboxed |
| 4 | `email.reply_with_context` | Reply to an Email Thread with Context | email | medium | 180s | sandboxed |
| 5 | `email.thread_summary_reply` | Summarize Thread and Reply to All Open Items | email | hard | 300s | sandboxed |
| 6 | `openclaw_email_composition` | OpenClaw Email Composition | email | medium | 300s | sandboxed |
| 7 | `general.algorithm_trace` | Trace Dijkstra's Shortest Path Algorithm | general | hard | 180s | sandboxed |
| 8 | `general.base_conversion` | Multi-Base Number System Conversions | general | medium | 120s | sandboxed |
| 9 | `general.cipher_decode` | Multi-Layer Cipher Decoding | general | medium | 120s | sandboxed |
| 10 | `general.code_output_prediction` | Predict Python Program Output | general | hard | 120s | sandboxed |
| 11 | `general.data_extraction` | Extract Structured Data from Messy Text | general | medium | 120s | sandboxed |
| 12 | `general.dependency_resolution` | Topological Sort for Package Installation | general | medium | 120s | sandboxed |
| 13 | `general.excel_array_formulas` | Evaluate Complex Array and Lookup Formula Chains | general | hard | 300s | sandboxed |
| 14 | `general.excel_conditional_aggregation` | Excel SUMIFS, COUNTIFS, and AVERAGEIFS Evaluation | general | medium | 240s | sandboxed |
| 15 | `general.excel_cross_sheet_reconciliation` | Cross-Sheet Data Reconciliation and Discrepancy Report | general | hard | 300s | sandboxed |
| 16 | `general.excel_data_validation` | Spreadsheet Data Validation and Error Detection | general | medium | 240s | sandboxed |
| 17 | `general.excel_financial_model` | Build Financial Projection Model from Assumptions | general | hard | 300s | sandboxed |
| 18 | `general.excel_formula_chain` | Evaluate Chained Excel Formulas with Circular Dependencies | general | hard | 240s | sandboxed |
| 19 | `general.excel_pivot_table` | Compute Pivot Table from Raw Transaction Data | general | hard | 240s | sandboxed |
| 20 | `general.excel_what_if_analysis` | Excel What-If Scenario and Goal Seek Analysis | general | hard | 300s | sandboxed |
| 21 | `general.file_organizer` | Organize Files into Categorized Directories | general | easy | 180s | sandboxed |
| 22 | `general.git_conflict_resolution` | Resolve Git Merge Conflicts | general | hard | 150s | sandboxed |
| 23 | `general.json_transform` | Complex JSON Data Transformation | general | medium | 150s | sandboxed |
| 24 | `general.logic_grid_puzzle` | Solve a Logic Grid Puzzle | general | hard | 180s | sandboxed |
| 25 | `general.math_word_problem` | Multi-Step Mathematical Word Problem | general | medium | 120s | sandboxed |
| 26 | `general.regex_match` | Evaluate Regular Expression Matches | general | medium | 120s | sandboxed |
| 27 | `general.schedule_planner` | Create an Optimized Daily Schedule | general | medium | 240s | sandboxed |
| 28 | `general.sql_query_result` | Compute SQL Query Result on Given Data | general | hard | 180s | sandboxed |
| 29 | `general.state_machine_trace` | Trace a State Machine on Input Sequence | general | hard | 180s | sandboxed |
| 30 | `openclaw_code_review` | OpenClaw Code Review | general | hard | 400s | sandboxed |
| 31 | `openclaw_currency_analysis` | Currency Exchange Rate Analysis | general | hard | 600s | sandboxed |
| 32 | `openclaw_document_summarization` | OpenClaw Document Summarization | summarization | medium | 350s | sandboxed |
| 33 | `summarization.daily_standup` | Generate Daily Work Summary from Multiple Sources | summarization | medium | 180s | sandboxed |
| 34 | `summarization.meeting_notes` | Summarize Meeting Transcript into Structured Notes | summarization | easy | 180s | sandboxed |
| 35 | `summarization.multi_source` | Multi-Source Executive Summary | summarization | hard | 300s | sandboxed |

### Evaluators

- **Exact Match** -- String comparison with sequence matching, contains-list checking, and email format validation
- **Rubric** -- Criterion-based scoring with keyword/phrase detection heuristics
- **LLM Judge** -- Uses OpenAI or Anthropic APIs to score responses, with graceful fallback to heuristic scoring
- **Composite** -- Combines multiple evaluators into a single pipeline

### Agent Adapters

- **Dummy Adapter** -- Returns canned responses for framework testing
- **Subprocess Adapter** -- Runs external agents as subprocesses with command templates (`{instruction}`, `{context_file}`, `{task_id}`)
- **OpenClaw Adapter** -- Integrates with OpenClaw agents for real-world task evaluation 🦞
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

# Run OpenClaw agent tests 🦞
clawarena run --agent openclaw --agent-id claude --category openclaw

# View results
clawarena results list
clawarena leaderboard
```

## Example: Email Task Run

```
$ python3 scripts/run_email_tasks.py

────────────────────────────────────────────────────────────
ClawArena — Email Task Run
  Sender  : yonyonlau@gmail.com
  Receiver: yangliu.real@gmail.com
  Tasks   : 4
────────────────────────────────────────────────────────────

[1/4] Compose a Professional Email
  id         : email.compose_simple
  difficulty : easy
  timeout    : 120s
  agent      : OK  (in=380 out=150 tokens)
  sending    : OK → yangliu.real@gmail.com
  score      : 42.3%  (correctness=15  completeness=17  efficiency=80  robustness=100)
  preview    : **Subject:** Q3 Feature Prioritization Meeting ...

[2/4] Reply to an Email Thread with Context
  id         : email.reply_with_context
  difficulty : medium
  timeout    : 180s
  agent      : OK  (in=718 out=243 tokens)
  sending    : OK → yangliu.real@gmail.com
  score      : 42.9%  (correctness=17  completeness=17  efficiency=80  robustness=100)
  preview    : **Subject:** Re: v2.4 Regression Test Results ...

[3/4] Summarize Thread and Reply to All Open Items
  id         : email.thread_summary_reply
  difficulty : hard
  timeout    : 300s
  agent      : OK  (in=1318 out=564 tokens)
  sending    : OK → yangliu.real@gmail.com
  score      : 47.7%  (correctness=40  completeness=18  efficiency=50  robustness=100)
  preview    : **Subject:** Re: Project Atlas Launch Updates ...

[4/4] OpenClaw Email Composition
  id         : openclaw_email_composition
  difficulty : medium
  timeout    : 300s
  agent      : OK  (in=348 out=182 tokens)
  sending    : OK → yangliu.real@gmail.com
  score      : 43.5%  (correctness=35  completeness=20  efficiency=30  robustness=100)
  preview    : **Subject:** Feedback Request: ClawArena AI Benchmarking Framework Proposal ...

────────────────────────────────────────────────────────────
RESULTS SUMMARY
────────────────────────────────────────────────────────────
  Emails sent : 4/4
  Failures    : 0
  Avg score   : 44.1%

Task                                             Score   Sent
───────────────────────────────────────────── ──────── ──────
email.compose_simple                             42.3%      ✓
email.reply_with_context                         42.9%      ✓
email.thread_summary_reply                       47.7%      ✓
openclaw_email_composition                       43.5%      ✓
────────────────────────────────────────────────────────────
```

## Project Structure

```
src/clawarena/
  core/           # Data models -- Task, AgentAdapter, Evaluator, Result, Scoring
  tasks/          # YAML loader, registry, and 10 built-in task definitions
  evaluators/     # Exact match, rubric, LLM judge, and composite evaluators
  adapters/       # Adapter registry, dummy, subprocess, and OpenClaw adapters 🦞
  engine/         # Run engine, pricing table, and sandbox isolation
  storage/        # Abstract backend and JSON file store
  reporting/      # Rich table rendering and leaderboard display
  cli.py          # Click-based CLI entry point
tests/            # Unit tests across all modules
tasks/examples/   # Example task YAML for reference
tasks/openclaw/   # OpenClaw-specific task definitions 🦞
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

## OpenClaw Integration 🦞

ClawArena includes native support for testing OpenClaw agents (lobsters) on real-world tasks. This integration allows you to evaluate any OpenClaw agent within the standardized benchmarking framework.

### Key Features

- **OpenClaw Agent Adapter**: Seamless integration with OpenClaw's agent execution system
- **Specialized Task Suite**: Pre-defined tasks optimized for OpenClaw agent evaluation
- **Sandboxed Execution**: Isolated task execution with proper workspace management
- **Comprehensive Metrics**: Detailed performance analytics for OpenClaw agents

### Getting Started with OpenClaw

1. **Install OpenClaw**: Ensure OpenClaw is installed and in your PATH
2. **Run OpenClaw Tests**:
   ```bash
   # Test Claude agent on OpenClaw tasks
   clawarena run --agent openclaw --agent-id claude --category openclaw
   
   # Test GPT-4 agent on specific task
   clawarena run --agent openclaw --agent-id gpt-4 --task openclaw_email_composition
   
   # Compare multiple agents
   clawarena run --agent openclaw --agent-id claude --agent openclaw --agent-id gpt-4 --agent dummy
   ```

3. **View Results**:
   ```bash
   clawarena leaderboard
   clawarena results list
   ```

### Available OpenClaw Tasks

- **Email Composition**: Professional email writing with context awareness
- **Code Review**: Python code analysis and improvement suggestions
- **Document Summarization**: Technical documentation summarization

For detailed documentation, see [OPENCLAW_INTEGRATION.md](docs/OPENCLAW_INTEGRATION.md).

## Project Structure

The project has been organized with a clear directory structure:

```
ClawArena/
├── src/                          # Source code
├── tasks/                        # Task definitions (YAML)
├── tests/                        # Test files
│   ├── openclaw/                 # OpenClaw integration tests
│   └── debug/                    # Debug scripts
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
└── results/                      # Test results
```

For complete directory structure details, see [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md).

## License

Apache 2.0
