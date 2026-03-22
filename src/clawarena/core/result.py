from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from clawarena.core.agent import AgentInfo, AgentResponse, TokenUsage


@dataclass
class TaskScore:
    correctness: float = 0.0
    completeness: float = 0.0
    efficiency: float = 0.0
    robustness: float = 0.0
    overall: float = 0.0
    evaluator_details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CostEstimate:
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    pricing_model: str = ""


@dataclass
class TaskResult:
    task_id: str
    task_name: str
    agent_response: AgentResponse
    score: TaskScore
    cost: CostEstimate
    passed: bool
    error: str | None = None


@dataclass
class RunResult:
    agent: AgentInfo
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    task_results: list[TaskResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    aggregate_score: float = 0.0
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
    total_cost: CostEstimate = field(default_factory=CostEstimate)
    total_duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
