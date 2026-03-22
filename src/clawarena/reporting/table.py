from __future__ import annotations

from rich.console import Console
from rich.table import Table

from clawarena.core.result import RunResult
from clawarena.core.scoring import Leaderboard, LeaderboardEntry


def render_leaderboard(leaderboard: Leaderboard, format: str = "table") -> str:
    if format == "table":
        return _render_rich_table(leaderboard)
    elif format == "csv":
        return _render_csv(leaderboard)
    elif format == "json":
        return _render_json(leaderboard)
    elif format == "markdown":
        return _render_markdown(leaderboard)
    else:
        raise ValueError(f"Unknown format: {format}")


def print_leaderboard(leaderboard: Leaderboard, format: str = "table") -> None:
    if format == "table":
        console = Console()
        table = _build_rich_table(leaderboard)
        console.print(table)
    else:
        print(render_leaderboard(leaderboard, format))


def render_run_result(result: RunResult) -> None:
    console = Console()

    console.print(f"\n[bold]Run: {result.run_id}[/bold]")
    console.print(f"Agent: {result.agent.name} v{result.agent.version} ({result.agent.model})")
    console.print(f"Score: {result.aggregate_score * 100:.1f}/100")
    console.print(f"Cost: ${result.total_cost.total_cost_usd:.6f}")
    console.print(f"Tokens: {result.total_tokens.total_tokens:,}")
    console.print(f"Duration: {result.total_duration_seconds:.2f}s")
    console.print()

    table = Table(title="Task Results")
    table.add_column("Task", style="cyan")
    table.add_column("Pass", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Correct", justify="right")
    table.add_column("Complete", justify="right")
    table.add_column("Efficient", justify="right")
    table.add_column("Robust", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Time", justify="right")

    for tr in result.task_results:
        pass_str = "[green]PASS[/green]" if tr.passed else "[red]FAIL[/red]"
        table.add_row(
            tr.task_id,
            pass_str,
            f"{tr.score.overall * 100:.1f}",
            f"{tr.score.correctness * 100:.1f}",
            f"{tr.score.completeness * 100:.1f}",
            f"{tr.score.efficiency * 100:.1f}",
            f"{tr.score.robustness * 100:.1f}",
            f"${tr.cost.total_cost_usd:.6f}",
            f"{tr.agent_response.duration_seconds:.2f}s",
        )

    console.print(table)


def _build_rich_table(leaderboard: Leaderboard) -> Table:
    table = Table(title="ClawArena Leaderboard")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Agent", style="cyan")
    table.add_column("Model", style="dim")
    table.add_column("Score", justify="right", style="bold green")
    table.add_column("Correct", justify="right")
    table.add_column("Complete", justify="right")
    table.add_column("Efficient", justify="right")
    table.add_column("Robust", justify="right")
    table.add_column("Pass Rate", justify="right")
    table.add_column("Cost", justify="right", style="yellow")
    table.add_column("Tokens", justify="right")
    table.add_column("Avg Time", justify="right")

    for e in leaderboard.entries:
        table.add_row(
            str(e.rank),
            f"{e.agent_name} v{e.agent_version}",
            e.model,
            f"{e.overall_score:.1f}",
            f"{e.correctness_avg:.1f}",
            f"{e.completeness_avg:.1f}",
            f"{e.efficiency_avg:.1f}",
            f"{e.robustness_avg:.1f}",
            f"{e.tasks_passed}/{e.tasks_total}",
            f"${e.total_cost_usd:.4f}",
            f"{e.total_tokens:,}",
            f"{e.avg_duration_seconds:.2f}s",
        )

    return table


def _render_rich_table(leaderboard: Leaderboard) -> str:
    console = Console(record=True, width=140)
    console.print(_build_rich_table(leaderboard))
    return console.export_text()


def _render_csv(leaderboard: Leaderboard) -> str:
    header = "rank,agent,version,model,score,correctness,completeness,efficiency,robustness,pass_rate,cost_usd,tokens,avg_time_s"
    lines = [header]
    for e in leaderboard.entries:
        lines.append(
            f"{e.rank},{e.agent_name},{e.agent_version},{e.model},"
            f"{e.overall_score},{e.correctness_avg},{e.completeness_avg},"
            f"{e.efficiency_avg},{e.robustness_avg},"
            f"{e.tasks_passed}/{e.tasks_total},{e.total_cost_usd:.6f},"
            f"{e.total_tokens},{e.avg_duration_seconds:.3f}"
        )
    return "\n".join(lines)


def _render_json(leaderboard: Leaderboard) -> str:
    import json
    from dataclasses import asdict

    return json.dumps([asdict(e) for e in leaderboard.entries], indent=2)


def _render_markdown(leaderboard: Leaderboard) -> str:
    lines = [
        "| # | Agent | Model | Score | Pass Rate | Cost | Tokens |",
        "|---|-------|-------|-------|-----------|------|--------|",
    ]
    for e in leaderboard.entries:
        lines.append(
            f"| {e.rank} | {e.agent_name} v{e.agent_version} | {e.model} | "
            f"{e.overall_score:.1f} | {e.tasks_passed}/{e.tasks_total} | "
            f"${e.total_cost_usd:.4f} | {e.total_tokens:,} |"
        )
    return "\n".join(lines)
