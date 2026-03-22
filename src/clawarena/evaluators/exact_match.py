"""Exact-match evaluator with optional contains and format checks."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from clawarena.core.agent import AgentResponse
from clawarena.core.evaluator import Evaluator
from clawarena.core.result import TaskScore
from clawarena.core.task import Task


class ExactMatchEvaluator(Evaluator):
    """Evaluates agent output by comparing it against ``task.expected_output``.

    Scoring strategy
    ----------------
    * **correctness** -- Sequence-match ratio between the agent output and the
      expected output.  Falls back to 0.0 when ``expected_output`` is *None*.
    * **completeness** -- 1.0 if every string in the ``contains`` list is
      present in the output, otherwise the fraction of found strings.
    * **efficiency** -- Penalises overly verbose responses.  A response whose
      length is <= 2x the expected output length receives 1.0; the score
      decreases linearly up to 5x, after which it is clamped to 0.2.
    * **robustness** -- 1.0 when the agent reported no error, 0.0 otherwise.
    * **overall** -- Weighted average:
      ``0.40 * correctness + 0.25 * completeness + 0.15 * efficiency + 0.20 * robustness``.

    Config keys
    -----------
    contains : list[str]
        Substrings that must all appear in the agent output.
    format : str
        Structural format to check.  Currently supported: ``"email"``
        (expects ``Subject:``, ``To:``, and ``Body:`` headers).
    case_sensitive : bool
        Whether comparisons are case-sensitive (default ``True``).
    """

    @property
    def name(self) -> str:
        return "exact_match"

    async def evaluate(
        self,
        task: Task,
        response: AgentResponse,
        config: dict[str, Any] | None = None,
    ) -> TaskScore:
        config = config or {}
        output = _to_str(response.output)
        expected = _to_str(task.expected_output) if task.expected_output is not None else None

        case_sensitive: bool = config.get("case_sensitive", True)
        contains: list[str] = config.get("contains", [])
        fmt: str | None = config.get("format")

        cmp_output = output if case_sensitive else output.lower()

        # -- correctness -------------------------------------------------------
        correctness = _compute_correctness(cmp_output, expected, case_sensitive)

        # -- completeness ------------------------------------------------------
        completeness = _compute_completeness(cmp_output, contains, case_sensitive, fmt)

        # -- efficiency --------------------------------------------------------
        efficiency = _compute_efficiency(output, expected)

        # -- robustness --------------------------------------------------------
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
                "contains_results": {
                    s: (s.lower() if not case_sensitive else s) in cmp_output
                    for s in contains
                },
                "format_check": fmt,
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_str(value: Any) -> str:
    """Coerce an arbitrary value to its string representation."""
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _compute_correctness(output: str, expected: str | None, case_sensitive: bool) -> float:
    """Sequence-match ratio between *output* and *expected*."""
    if expected is None:
        return 0.0
    cmp_expected = expected if case_sensitive else expected.lower()
    if output == cmp_expected:
        return 1.0
    return SequenceMatcher(None, output, cmp_expected).ratio()


def _compute_completeness(
    output: str,
    contains: list[str],
    case_sensitive: bool,
    fmt: str | None,
) -> float:
    """Fraction of ``contains`` items found + optional format bonus."""
    scores: list[float] = []

    # Contains check
    if contains:
        found = sum(
            1
            for s in contains
            if (s if case_sensitive else s.lower()) in output
        )
        scores.append(found / len(contains))

    # Format check
    if fmt is not None:
        scores.append(_check_format(output, fmt))

    if not scores:
        return 1.0  # nothing to check -- vacuously complete
    return sum(scores) / len(scores)


_EMAIL_HEADERS = [
    re.compile(r"(?m)^Subject\s*:", re.IGNORECASE),
    re.compile(r"(?m)^To\s*:", re.IGNORECASE),
    re.compile(r"(?m)^Body\s*:", re.IGNORECASE),
]


def _check_format(output: str, fmt: str) -> float:
    """Return 1.0 if *output* satisfies the structural *fmt*, else a partial score."""
    if fmt == "email":
        matched = sum(1 for pat in _EMAIL_HEADERS if pat.search(output))
        return matched / len(_EMAIL_HEADERS)
    # Unknown format -- pass through
    return 1.0


def _compute_efficiency(output: str, expected: str | None) -> float:
    """Penalise overly long responses relative to the expected output."""
    if expected is None or len(expected) == 0:
        # Without a reference length, give a mild penalty for very long output.
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
    # Linear interpolation between 2x (1.0) and 5x (0.2)
    return 1.0 - 0.8 * (ratio - 2.0) / 3.0
