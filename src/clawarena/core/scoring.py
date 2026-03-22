from __future__ import annotations

from dataclasses import dataclass, field

from clawarena.core.result import RunResult


@dataclass(frozen=True)
class ScoreWeights:
    correctness: float = 0.40
    completeness: float = 0.25
    efficiency: float = 0.20
    robustness: float = 0.15

    def __post_init__(self) -> None:
        total = self.correctness + self.completeness + self.efficiency + self.robustness
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass
class LeaderboardEntry:
    rank: int
    agent_name: str
    agent_version: str
    model: str
    overall_score: float
    correctness_avg: float
    completeness_avg: float
    efficiency_avg: float
    robustness_avg: float
    total_cost_usd: float
    total_tokens: int
    avg_duration_seconds: float
    tasks_passed: int
    tasks_total: int
    run_id: str


@dataclass
class Leaderboard:
    entries: list[LeaderboardEntry] = field(default_factory=list)

    @classmethod
    def from_runs(cls, runs: list[RunResult]) -> Leaderboard:
        entries: list[LeaderboardEntry] = []

        for run in runs:
            if not run.task_results:
                continue

            n = len(run.task_results)
            correctness_avg = sum(r.score.correctness for r in run.task_results) / n
            completeness_avg = sum(r.score.completeness for r in run.task_results) / n
            efficiency_avg = sum(r.score.efficiency for r in run.task_results) / n
            robustness_avg = sum(r.score.robustness for r in run.task_results) / n

            entries.append(
                LeaderboardEntry(
                    rank=0,
                    agent_name=run.agent.name,
                    agent_version=run.agent.version,
                    model=run.agent.model,
                    overall_score=round(run.aggregate_score * 100, 2),
                    correctness_avg=round(correctness_avg * 100, 2),
                    completeness_avg=round(completeness_avg * 100, 2),
                    efficiency_avg=round(efficiency_avg * 100, 2),
                    robustness_avg=round(robustness_avg * 100, 2),
                    total_cost_usd=round(run.total_cost.total_cost_usd, 6),
                    total_tokens=run.total_tokens.total_tokens,
                    avg_duration_seconds=round(run.total_duration_seconds / n, 3),
                    tasks_passed=sum(1 for r in run.task_results if r.passed),
                    tasks_total=n,
                    run_id=run.run_id,
                )
            )

        # Sort: score desc, cost asc, speed asc
        entries.sort(key=lambda e: (-e.overall_score, e.total_cost_usd, e.avg_duration_seconds))

        for i, entry in enumerate(entries, start=1):
            entry.rank = i

        return cls(entries=entries)
