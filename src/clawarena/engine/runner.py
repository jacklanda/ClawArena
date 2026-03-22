from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from clawarena.core.agent import AgentAdapter, AgentResponse, TokenUsage
from clawarena.core.evaluator import Evaluator
from clawarena.core.result import CostEstimate, RunResult, TaskResult, TaskScore
from clawarena.core.task import Task, TaskSuite
from clawarena.engine.pricing import PricingTable
from clawarena.engine.sandbox import Sandbox

logger = logging.getLogger(__name__)


@dataclass
class RunConfig:
    timeout_override: int | None = None
    pass_threshold: float = 0.70
    parallel_tasks: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class RunEngine:
    def __init__(
        self,
        evaluator_registry: dict[str, Evaluator],
        pricing: PricingTable | None = None,
    ) -> None:
        self._evaluators = evaluator_registry
        self._pricing = pricing or PricingTable()

    async def run(
        self,
        suite: TaskSuite,
        adapters: list[AgentAdapter],
        config: RunConfig | None = None,
    ) -> list[RunResult]:
        config = config or RunConfig()
        results: list[RunResult] = []

        for adapter in adapters:
            logger.info("Running agent: %s", adapter.info().name)
            await adapter.setup()
            try:
                run_result = await self._run_agent(adapter, suite, config)
                results.append(run_result)
            finally:
                await adapter.teardown()

        return results

    async def _run_agent(
        self,
        adapter: AgentAdapter,
        suite: TaskSuite,
        config: RunConfig,
    ) -> RunResult:
        run_result = RunResult(agent=adapter.info())

        for task in suite.tasks:
            logger.info("  Task: %s", task.id)
            task_result = await self._run_single_task(adapter, task, config)
            run_result.task_results.append(task_result)

        run_result = self._finalize(run_result)
        return run_result

    async def _run_single_task(
        self,
        adapter: AgentAdapter,
        task: Task,
        config: RunConfig,
    ) -> TaskResult:
        timeout = config.timeout_override or task.timeout_seconds

        async with Sandbox(task):
            try:
                response = await asyncio.wait_for(
                    adapter.run_task(task),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                response = AgentResponse(output=None, error="timeout")
            except Exception as e:
                response = AgentResponse(output=None, error=str(e))

        score = await self._evaluate(task, response)
        cost = self._pricing.estimate(response.token_usage, adapter.info().model)

        threshold = task.evaluation.config.get("pass_threshold", config.pass_threshold)

        return TaskResult(
            task_id=task.id,
            task_name=task.name,
            agent_response=response,
            score=score,
            cost=cost,
            passed=score.overall >= threshold,
            error=response.error,
        )

    async def _evaluate(self, task: Task, response: AgentResponse) -> TaskScore:
        evaluator_name = task.evaluation.evaluator

        if evaluator_name not in self._evaluators:
            logger.warning("Evaluator %r not found, using default scoring", evaluator_name)
            return TaskScore(
                correctness=0.5,
                completeness=0.5,
                efficiency=0.5,
                robustness=1.0 if response.error is None else 0.0,
                overall=0.5 if response.error is None else 0.0,
            )

        evaluator = self._evaluators[evaluator_name]
        return await evaluator.evaluate(task, response, task.evaluation.config)

    def _finalize(self, run_result: RunResult) -> RunResult:
        run_result.completed_at = datetime.now(timezone.utc)

        if not run_result.task_results:
            return run_result

        total_input = sum(
            r.agent_response.token_usage.input_tokens for r in run_result.task_results
        )
        total_output = sum(
            r.agent_response.token_usage.output_tokens for r in run_result.task_results
        )
        run_result.total_tokens = TokenUsage(
            input_tokens=total_input,
            output_tokens=total_output,
            total_tokens=total_input + total_output,
        )

        run_result.total_cost = CostEstimate(
            input_cost_usd=sum(r.cost.input_cost_usd for r in run_result.task_results),
            output_cost_usd=sum(r.cost.output_cost_usd for r in run_result.task_results),
            total_cost_usd=sum(r.cost.total_cost_usd for r in run_result.task_results),
        )

        run_result.total_duration_seconds = sum(
            r.agent_response.duration_seconds for r in run_result.task_results
        )

        scores = [r.score.overall for r in run_result.task_results]
        run_result.aggregate_score = sum(scores) / len(scores) if scores else 0.0

        return run_result
