from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from clawarena import __version__

console = Console()


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


@click.group()
@click.version_option(version=__version__, prog_name="clawarena")
def main() -> None:
    """ClawArena — An agent benchmarking arena for evaluating AI agents on real-world tasks."""
    pass


# --- run ---


@main.command()
@click.option("--agent", "-a", multiple=True, required=True, help="Agent adapter name(s)")
@click.option("--category", "-c", default=None, help="Filter tasks by category")
@click.option("--difficulty", "-d", default=None, help="Filter tasks by difficulty")
@click.option("--task", "-t", default=None, help="Run a specific task by ID")
@click.option("--timeout", default=None, type=int, help="Override task timeout (seconds)")
@click.option("--output-dir", "-o", default="results", help="Results output directory")
@click.option("--task-dir", default=None, help="Additional task directory")
def run(
    agent: tuple[str, ...],
    category: str | None,
    difficulty: str | None,
    task: str | None,
    timeout: int | None,
    output_dir: str,
    task_dir: str | None,
) -> None:
    """Run benchmark tasks against one or more agents."""
    _run_async(_run_impl(agent, category, difficulty, task, timeout, output_dir, task_dir))


async def _run_impl(
    agent_names: tuple[str, ...],
    category: str | None,
    difficulty: str | None,
    task_id: str | None,
    timeout: int | None,
    output_dir: str,
    task_dir: str | None,
) -> None:
    from clawarena.adapters.registry import AdapterRegistry
    from clawarena.core.task import TaskCategory, TaskDifficulty
    from clawarena.engine.runner import RunConfig, RunEngine
    from clawarena.evaluators import get_evaluator_registry
    from clawarena.reporting.table import print_leaderboard, render_run_result
    from clawarena.storage.json_store import JsonFileStore
    from clawarena.tasks.registry import TaskRegistry

    # Load tasks
    registry = TaskRegistry()
    if task_dir:
        registry.add_directory(Path(task_dir))

    suite = registry.as_suite("ClawArena Benchmark")

    if task_id:
        try:
            t = registry.get(task_id)
        except KeyError:
            console.print(f"[red]Task not found: {task_id}[/red]")
            sys.exit(1)
        from clawarena.core.task import TaskSuite

        suite = TaskSuite(name="single", description="Single task run", tasks=[t])
    else:
        if category:
            suite = suite.filter_by_category(TaskCategory(category))
        if difficulty:
            suite = suite.filter_by_difficulty(TaskDifficulty(difficulty))

    if len(suite) == 0:
        console.print("[red]No tasks matched the given filters.[/red]")
        sys.exit(1)

    console.print(f"[bold]Running {len(suite)} tasks...[/bold]\n")

    # Load adapters
    adapter_registry = AdapterRegistry()
    adapter_registry.discover_plugins()
    adapters = []
    for name in agent_names:
        try:
            adapters.append(adapter_registry.get(name))
        except KeyError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)

    # Run
    evaluator_reg = get_evaluator_registry()
    engine = RunEngine(evaluator_registry=evaluator_reg)
    config = RunConfig(timeout_override=timeout)
    results = await engine.run(suite, adapters, config)

    # Store
    storage = JsonFileStore(base_dir=output_dir)
    for result in results:
        path = await storage.save_run(result)
        console.print(f"[dim]Saved: {path}[/dim]")

    # Display
    for result in results:
        render_run_result(result)

    if len(results) > 1:
        from clawarena.core.scoring import Leaderboard

        leaderboard = Leaderboard.from_runs(results)
        console.print()
        print_leaderboard(leaderboard)


# --- list ---


@main.group("list")
def list_cmd() -> None:
    """List available resources."""
    pass


@list_cmd.command("tasks")
@click.option("--category", "-c", default=None, help="Filter by category")
@click.option("--difficulty", "-d", default=None, help="Filter by difficulty")
def list_tasks(category: str | None, difficulty: str | None) -> None:
    """List available benchmark tasks."""
    from rich.table import Table

    from clawarena.core.task import TaskCategory, TaskDifficulty
    from clawarena.tasks.registry import TaskRegistry

    registry = TaskRegistry()
    tasks = registry.list_all()

    if category:
        tasks = [t for t in tasks if t.category == TaskCategory(category)]
    if difficulty:
        tasks = [t for t in tasks if t.difficulty == TaskDifficulty(difficulty)]

    table = Table(title=f"Available Tasks ({len(tasks)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Category", style="green")
    table.add_column("Difficulty")
    table.add_column("Timeout", justify="right")
    table.add_column("Mode")

    diff_colors = {"easy": "green", "medium": "yellow", "hard": "red"}

    for t in sorted(tasks, key=lambda x: x.id):
        color = diff_colors.get(t.difficulty.value, "white")
        table.add_row(
            t.id,
            t.name,
            t.category.value,
            f"[{color}]{t.difficulty.value}[/{color}]",
            f"{t.timeout_seconds}s",
            t.execution_mode.value,
        )

    console.print(table)


@list_cmd.command("agents")
def list_agents() -> None:
    """List available agent adapters."""
    from clawarena.adapters.registry import AdapterRegistry

    registry = AdapterRegistry()
    registry.discover_plugins()

    console.print("[bold]Available Agent Adapters:[/bold]\n")
    for name in registry.list_available():
        try:
            adapter = registry.get(name)
            info = adapter.info()
            console.print(f"  [cyan]{name}[/cyan] — {info.name} v{info.version} ({info.model})")
        except TypeError:
            console.print(f"  [cyan]{name}[/cyan] — (requires configuration)")
    console.print()


@list_cmd.command("evaluators")
def list_evaluators() -> None:
    """List available evaluators."""
    from clawarena.evaluators import get_evaluator_registry

    reg = get_evaluator_registry()

    console.print("[bold]Available Evaluators:[/bold]\n")
    for name in sorted(reg.keys()):
        console.print(f"  [cyan]{name}[/cyan]")
    console.print()


# --- results ---


@main.group()
def results() -> None:
    """View and manage run results."""
    pass


@results.command("show")
@click.argument("run_id")
@click.option("--output-dir", "-o", default="results", help="Results directory")
def results_show(run_id: str, output_dir: str) -> None:
    """Show detailed results for a run."""
    _run_async(_results_show_impl(run_id, output_dir))


async def _results_show_impl(run_id: str, output_dir: str) -> None:
    from clawarena.reporting.table import render_run_result
    from clawarena.storage.json_store import JsonFileStore

    storage = JsonFileStore(base_dir=output_dir)
    result = await storage.load_run(run_id)
    if result is None:
        console.print(f"[red]Run not found: {run_id}[/red]")
        sys.exit(1)
    render_run_result(result)


@results.command("list")
@click.option("--agent", "-a", default=None, help="Filter by agent name")
@click.option("--limit", "-n", default=20, help="Max results to show")
@click.option("--output-dir", "-o", default="results", help="Results directory")
def results_list(agent: str | None, limit: int, output_dir: str) -> None:
    """List all runs."""
    _run_async(_results_list_impl(agent, limit, output_dir))


async def _results_list_impl(agent: str | None, limit: int, output_dir: str) -> None:
    from rich.table import Table

    from clawarena.storage.json_store import JsonFileStore

    storage = JsonFileStore(base_dir=output_dir)
    runs = await storage.list_runs(agent_name=agent, limit=limit)

    if not runs:
        console.print("[dim]No runs found.[/dim]")
        return

    table = Table(title="Runs")
    table.add_column("Run ID", style="cyan")
    table.add_column("Agent")
    table.add_column("Model", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Date")

    for r in runs:
        table.add_row(
            r["run_id"],
            r["agent"],
            r.get("model", ""),
            f"{r.get('score', 0) * 100:.1f}",
            f"${r.get('cost_usd', 0):.4f}",
            r.get("date", "")[:19],
        )

    console.print(table)


@results.command("compare")
@click.argument("run_id_1")
@click.argument("run_id_2")
@click.option("--output-dir", "-o", default="results", help="Results directory")
def results_compare(run_id_1: str, run_id_2: str, output_dir: str) -> None:
    """Compare two runs side by side."""
    _run_async(_results_compare_impl(run_id_1, run_id_2, output_dir))


async def _results_compare_impl(run_id_1: str, run_id_2: str, output_dir: str) -> None:
    from rich.table import Table

    from clawarena.core.scoring import Leaderboard
    from clawarena.reporting.table import print_leaderboard
    from clawarena.storage.json_store import JsonFileStore

    storage = JsonFileStore(base_dir=output_dir)
    r1 = await storage.load_run(run_id_1)
    r2 = await storage.load_run(run_id_2)

    if r1 is None:
        console.print(f"[red]Run not found: {run_id_1}[/red]")
        sys.exit(1)
    if r2 is None:
        console.print(f"[red]Run not found: {run_id_2}[/red]")
        sys.exit(1)

    leaderboard = Leaderboard.from_runs([r1, r2])
    print_leaderboard(leaderboard)

    # Per-task comparison
    table = Table(title="Per-Task Comparison")
    table.add_column("Task", style="cyan")
    table.add_column(f"{r1.agent.name} Score", justify="right")
    table.add_column(f"{r2.agent.name} Score", justify="right")
    table.add_column("Delta", justify="right")

    tasks_1 = {tr.task_id: tr for tr in r1.task_results}
    tasks_2 = {tr.task_id: tr for tr in r2.task_results}
    all_task_ids = sorted(set(tasks_1.keys()) | set(tasks_2.keys()))

    for tid in all_task_ids:
        s1 = tasks_1[tid].score.overall * 100 if tid in tasks_1 else 0
        s2 = tasks_2[tid].score.overall * 100 if tid in tasks_2 else 0
        delta = s1 - s2
        delta_str = f"[green]+{delta:.1f}[/green]" if delta > 0 else f"[red]{delta:.1f}[/red]"
        if abs(delta) < 0.01:
            delta_str = "0.0"
        table.add_row(tid, f"{s1:.1f}", f"{s2:.1f}", delta_str)

    console.print(table)


# --- leaderboard ---


@main.command()
@click.option(
    "--format", "-f", "fmt", default="table", type=click.Choice(["table", "csv", "json", "markdown"])
)
@click.option("--sort", "-s", default="score", type=click.Choice(["score", "cost", "speed"]))
@click.option("--top", "-n", default=None, type=int, help="Show top N entries")
@click.option("--output-dir", "-o", default="results", help="Results directory")
def leaderboard(fmt: str, sort: str, top: int | None, output_dir: str) -> None:
    """Display the leaderboard from all runs."""
    _run_async(_leaderboard_impl(fmt, sort, top, output_dir))


async def _leaderboard_impl(fmt: str, sort: str, top: int | None, output_dir: str) -> None:
    from clawarena.reporting.leaderboard import compute_leaderboard
    from clawarena.reporting.table import print_leaderboard, render_leaderboard
    from clawarena.storage.json_store import JsonFileStore

    storage = JsonFileStore(base_dir=output_dir)
    lb = await compute_leaderboard(storage)

    if not lb.entries:
        console.print("[dim]No runs found. Run some benchmarks first.[/dim]")
        return

    if sort == "cost":
        lb.entries.sort(key=lambda e: (e.total_cost_usd, -e.overall_score))
        for i, e in enumerate(lb.entries, 1):
            e.rank = i
    elif sort == "speed":
        lb.entries.sort(key=lambda e: (e.avg_duration_seconds, -e.overall_score))
        for i, e in enumerate(lb.entries, 1):
            e.rank = i

    if top:
        lb.entries = lb.entries[:top]

    print_leaderboard(lb, format=fmt)


# --- validate ---


@main.command()
@click.argument("path", type=click.Path(exists=True))
def validate(path: str) -> None:
    """Validate a task YAML definition."""
    from clawarena.tasks.loader import load_task_from_yaml

    try:
        task = load_task_from_yaml(Path(path))
        console.print(f"[green]Valid![/green] Task: {task.id} ({task.name})")
        console.print(f"  Category: {task.category.value}")
        console.print(f"  Difficulty: {task.difficulty.value}")
        console.print(f"  Evaluator: {task.evaluation.evaluator}")
        console.print(f"  Timeout: {task.timeout_seconds}s")
    except Exception as e:
        console.print(f"[red]Invalid:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
