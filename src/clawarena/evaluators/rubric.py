"""Rubric-based evaluator with heuristic/keyword matching."""

from __future__ import annotations

import re
from typing import Any

from clawarena.core.agent import AgentResponse
from clawarena.core.evaluator import Evaluator
from clawarena.core.result import TaskScore
from clawarena.core.task import Task


class RubricEvaluator(Evaluator):
    """Score output against a list of weighted rubric criteria.

    For v0.1.0 every criterion is evaluated using lightweight heuristics:
    keyword/phrase detection and simple structural checks.  Each criterion
    yields a score in ``[0, 1]`` which is weighted by the criterion's
    ``weight``.  The weighted sum becomes the **correctness** dimension.

    Config format
    -------------
    .. code-block:: yaml

        criteria:
          - name: has_greeting
            description: "Email starts with appropriate greeting"
            weight: 0.15
            keywords: ["dear", "hello", "hi"]
          - name: covers_all_points
            description: "All key points addressed"
            weight: 0.40
            keywords: ["budget", "timeline", "deliverables"]
        pass_threshold: 0.70

    ``keywords`` is an optional convenience field.  When provided, the
    criterion score equals the fraction of keywords found in the output.
    When omitted, the evaluator falls back to a partial-match search
    using tokens extracted from the criterion *description*.
    """

    @property
    def name(self) -> str:
        return "rubric"

    async def evaluate(
        self,
        task: Task,
        response: AgentResponse,
        config: dict[str, Any] | None = None,
    ) -> TaskScore:
        config = config or {}
        criteria: list[dict[str, Any]] = config.get("criteria", [])
        pass_threshold: float = config.get("pass_threshold", 0.70)

        output = _to_str(response.output).lower()
        criterion_results: dict[str, dict[str, Any]] = {}
        weighted_total = 0.0
        weight_sum = 0.0

        for criterion in criteria:
            crit_name: str = criterion.get("name", "unnamed")
            description: str = criterion.get("description", "")
            weight: float = float(criterion.get("weight", 1.0))
            keywords: list[str] | None = criterion.get("keywords")

            score = _score_criterion(output, description, keywords)

            criterion_results[crit_name] = {
                "score": round(score, 4),
                "weight": weight,
                "description": description,
            }
            weighted_total += score * weight
            weight_sum += weight

        # Normalise into [0, 1]
        correctness = weighted_total / weight_sum if weight_sum > 0 else 0.0

        # Completeness: proportion of criteria that scored above the pass threshold
        if criteria:
            passed_count = sum(
                1
                for v in criterion_results.values()
                if v["score"] >= pass_threshold
            )
            completeness = passed_count / len(criteria)
        else:
            completeness = 1.0

        # Efficiency: based on response length — shorter is better, up to a point
        efficiency = _compute_efficiency(output, task.expected_output)

        # Robustness: 1.0 when no error was reported
        robustness = 1.0 if response.error is None else 0.0

        overall = (
            0.40 * correctness
            + 0.25 * completeness
            + 0.15 * efficiency
            + 0.20 * robustness
        )

        return TaskScore(
            correctness=round(correctness, 4),
            completeness=round(completeness, 4),
            efficiency=round(efficiency, 4),
            robustness=round(robustness, 4),
            overall=round(overall, 4),
            evaluator_details={
                "evaluator": self.name,
                "criteria": criterion_results,
                "pass_threshold": pass_threshold,
                "passed": correctness >= pass_threshold,
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "a an the is are was were be been being has have had do does did "
    "will would shall should may might can could of in to for on with "
    "at by from that this it and or but not".split()
)


def _to_str(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _extract_tokens(text: str) -> list[str]:
    """Extract meaningful lowercase tokens from *text*, dropping stop words."""
    tokens = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]


def _score_criterion(
    output: str,
    description: str,
    keywords: list[str] | None,
) -> float:
    """Heuristic score for a single criterion.

    If *keywords* is given, the score is the fraction of keywords found in
    *output*.  Otherwise, tokens are extracted from *description* and the
    fraction of those tokens found in the output is used as a fallback.
    """
    if keywords:
        if not keywords:
            return 0.0
        found = sum(1 for kw in keywords if kw.lower() in output)
        return found / len(keywords)

    # Fallback: partial match using description tokens
    tokens = _extract_tokens(description)
    if not tokens:
        return 0.0
    found = sum(1 for tok in tokens if tok in output)
    return found / len(tokens)


def _compute_efficiency(output: str, expected_output: Any) -> float:
    """Simple length-based efficiency heuristic."""
    expected = _to_str(expected_output)
    if not expected:
        if len(output) <= 500:
            return 1.0
        if len(output) <= 2000:
            return 0.8
        return 0.5

    ratio = len(output) / max(len(expected), 1)
    if ratio <= 2.0:
        return 1.0
    if ratio >= 5.0:
        return 0.2
    return 1.0 - 0.8 * (ratio - 2.0) / 3.0
