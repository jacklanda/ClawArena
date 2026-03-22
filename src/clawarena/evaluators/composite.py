"""Composite evaluator that combines multiple evaluators with weights."""

from __future__ import annotations

import logging
from typing import Any

from clawarena.core.agent import AgentResponse
from clawarena.core.evaluator import Evaluator
from clawarena.core.result import TaskScore
from clawarena.core.task import Task

logger = logging.getLogger(__name__)


class CompositeEvaluator(Evaluator):
    """Aggregate several evaluators into a single weighted score.

    Config format
    -------------
    .. code-block:: yaml

        evaluators:
          - evaluator: rubric
            weight: 0.6
            config:
              criteria:
                - name: has_greeting
                  description: "Email starts with appropriate greeting"
                  weight: 0.15
          - evaluator: llm_judge
            weight: 0.4
            config:
              judge_model: gpt-4o

    Each sub-evaluator is looked up via
    :func:`clawarena.evaluators.get_evaluator` and invoked independently.
    The resulting :class:`TaskScore` dimensions are combined as a
    weight-normalised average.
    """

    @property
    def name(self) -> str:
        return "composite"

    async def evaluate(
        self,
        task: Task,
        response: AgentResponse,
        config: dict[str, Any] | None = None,
    ) -> TaskScore:
        # Import here to avoid circular imports at module level.
        from clawarena.evaluators import get_evaluator

        config = config or {}
        evaluator_specs: list[dict[str, Any]] = config.get("evaluators", [])

        if not evaluator_specs:
            logger.warning("CompositeEvaluator received an empty evaluator list.")
            return TaskScore()

        sub_scores: list[tuple[float, TaskScore, str]] = []
        total_weight = 0.0

        for spec in evaluator_specs:
            evaluator_name: str = spec.get("evaluator", "")
            weight: float = float(spec.get("weight", 1.0))
            sub_config: dict[str, Any] = spec.get("config", {})

            try:
                evaluator = get_evaluator(evaluator_name)
            except KeyError:
                logger.error(
                    "Unknown evaluator %r in composite config; skipping.",
                    evaluator_name,
                )
                continue

            try:
                score = await evaluator.evaluate(task, response, sub_config)
            except Exception:
                logger.exception(
                    "Sub-evaluator %r raised an exception; skipping.",
                    evaluator_name,
                )
                continue

            sub_scores.append((weight, score, evaluator_name))
            total_weight += weight

        if not sub_scores or total_weight == 0.0:
            logger.warning("No sub-evaluators produced a score.")
            return TaskScore()

        # Weighted aggregation across dimensions
        correctness = sum(w * s.correctness for w, s, _ in sub_scores) / total_weight
        completeness = sum(w * s.completeness for w, s, _ in sub_scores) / total_weight
        efficiency = sum(w * s.efficiency for w, s, _ in sub_scores) / total_weight
        robustness = sum(w * s.robustness for w, s, _ in sub_scores) / total_weight
        overall = sum(w * s.overall for w, s, _ in sub_scores) / total_weight

        return TaskScore(
            correctness=round(correctness, 4),
            completeness=round(completeness, 4),
            efficiency=round(efficiency, 4),
            robustness=round(robustness, 4),
            overall=round(overall, 4),
            evaluator_details={
                "evaluator": self.name,
                "sub_evaluators": {
                    name: {
                        "weight": w,
                        "score": {
                            "correctness": s.correctness,
                            "completeness": s.completeness,
                            "efficiency": s.efficiency,
                            "robustness": s.robustness,
                            "overall": s.overall,
                        },
                        "details": s.evaluator_details,
                    }
                    for w, s, name in sub_scores
                },
            },
        )
