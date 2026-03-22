import pytest

from clawarena.core.scoring import Leaderboard, LeaderboardEntry, ScoreWeights


def test_score_weights_valid():
    w = ScoreWeights()
    assert abs(w.correctness + w.completeness + w.efficiency + w.robustness - 1.0) < 1e-6


def test_score_weights_invalid():
    with pytest.raises(ValueError, match="must sum to 1.0"):
        ScoreWeights(correctness=0.5, completeness=0.5, efficiency=0.5, robustness=0.5)


def test_leaderboard_ranking():
    from clawarena.core.agent import AgentInfo, TokenUsage
    from clawarena.core.result import CostEstimate, RunResult, TaskResult, TaskScore
    from clawarena.core.agent import AgentResponse

    def make_run(name, score, cost):
        agent = AgentInfo(name=name, version="1.0", model="test")
        resp = AgentResponse(
            output="out",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            duration_seconds=1.0,
        )
        tr = TaskResult(
            task_id="t1", task_name="T1", agent_response=resp,
            score=TaskScore(correctness=score, completeness=score, efficiency=score,
                          robustness=score, overall=score),
            cost=CostEstimate(total_cost_usd=cost),
            passed=score >= 0.7,
        )
        return RunResult(
            agent=agent, task_results=[tr], aggregate_score=score,
            total_cost=CostEstimate(total_cost_usd=cost),
            total_tokens=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            total_duration_seconds=1.0,
        )

    runs = [make_run("Bad", 0.3, 0.01), make_run("Good", 0.9, 0.05), make_run("Mid", 0.6, 0.03)]
    lb = Leaderboard.from_runs(runs)

    assert lb.entries[0].agent_name == "Good"
    assert lb.entries[0].rank == 1
    assert lb.entries[1].agent_name == "Mid"
    assert lb.entries[2].agent_name == "Bad"
