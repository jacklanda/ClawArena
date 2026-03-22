from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clawarena.core.agent import AgentInfo, AgentResponse, TokenUsage
from clawarena.core.result import CostEstimate, RunResult, TaskResult, TaskScore
from clawarena.storage.backend import StorageBackend


def _serialize(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _run_to_dict(result: RunResult) -> dict[str, Any]:
    d = asdict(result)
    return d


def _dict_to_run(data: dict[str, Any]) -> RunResult:
    agent = AgentInfo(**data["agent"])

    task_results = []
    for tr in data.get("task_results", []):
        token_usage = TokenUsage(**tr["agent_response"].get("token_usage", {}))
        agent_response = AgentResponse(
            output=tr["agent_response"]["output"],
            token_usage=token_usage,
            duration_seconds=tr["agent_response"].get("duration_seconds", 0.0),
            api_calls=tr["agent_response"].get("api_calls", 0),
            error=tr["agent_response"].get("error"),
            trace=tr["agent_response"].get("trace", []),
            raw_metadata=tr["agent_response"].get("raw_metadata", {}),
        )
        score = TaskScore(**tr["score"])
        cost = CostEstimate(**tr["cost"])
        task_results.append(
            TaskResult(
                task_id=tr["task_id"],
                task_name=tr["task_name"],
                agent_response=agent_response,
                score=score,
                cost=cost,
                passed=tr["passed"],
                error=tr.get("error"),
            )
        )

    total_tokens = TokenUsage(**data.get("total_tokens", {}))
    total_cost = CostEstimate(**data.get("total_cost", {}))

    started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else datetime.now(timezone.utc)
    completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None

    return RunResult(
        agent=agent,
        run_id=data["run_id"],
        task_results=task_results,
        started_at=started_at,
        completed_at=completed_at,
        aggregate_score=data.get("aggregate_score", 0.0),
        total_tokens=total_tokens,
        total_cost=total_cost,
        total_duration_seconds=data.get("total_duration_seconds", 0.0),
        metadata=data.get("metadata", {}),
    )


class JsonFileStore(StorageBackend):
    def __init__(self, base_dir: str | Path = "results") -> None:
        self._base_dir = Path(base_dir)
        self._runs_dir = self._base_dir / "runs"
        self._runs_dir.mkdir(parents=True, exist_ok=True)

    async def save_run(self, result: RunResult) -> str:
        date_str = result.started_at.strftime("%Y-%m-%d")
        filename = f"{date_str}_{result.run_id}_{result.agent.name}.json"
        filepath = self._runs_dir / filename

        data = _run_to_dict(result)
        filepath.write_text(json.dumps(data, default=_serialize, indent=2))

        self._update_index(result, filename)
        return str(filepath)

    async def load_run(self, run_id: str) -> RunResult | None:
        for filepath in self._runs_dir.glob("*.json"):
            if run_id in filepath.name:
                data = json.loads(filepath.read_text())
                return _dict_to_run(data)
        return None

    async def list_runs(
        self, agent_name: str | None = None, limit: int = 50
    ) -> list[dict[str, str]]:
        index_path = self._base_dir / "index.json"
        if not index_path.exists():
            return []

        index = json.loads(index_path.read_text())
        runs = index.get("runs", [])

        if agent_name:
            runs = [r for r in runs if r.get("agent") == agent_name]

        runs.sort(key=lambda r: r.get("date", ""), reverse=True)
        return runs[:limit]

    async def load_all_runs(self) -> list[RunResult]:
        results = []
        for filepath in sorted(self._runs_dir.glob("*.json")):
            data = json.loads(filepath.read_text())
            results.append(_dict_to_run(data))
        return results

    def _update_index(self, result: RunResult, filename: str) -> None:
        index_path = self._base_dir / "index.json"
        if index_path.exists():
            index = json.loads(index_path.read_text())
        else:
            index = {"runs": []}

        index["runs"].append(
            {
                "run_id": result.run_id,
                "agent": result.agent.name,
                "model": result.agent.model,
                "date": result.started_at.isoformat(),
                "score": round(result.aggregate_score, 4),
                "cost_usd": round(result.total_cost.total_cost_usd, 6),
                "file": filename,
            }
        )

        index_path.write_text(json.dumps(index, indent=2))
