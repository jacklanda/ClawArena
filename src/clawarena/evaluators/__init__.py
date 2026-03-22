"""Built-in evaluator implementations and registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from clawarena.evaluators.composite import CompositeEvaluator
from clawarena.evaluators.exact_match import ExactMatchEvaluator
from clawarena.evaluators.llm_judge import LLMJudgeEvaluator
from clawarena.evaluators.rubric import RubricEvaluator

if TYPE_CHECKING:
    from clawarena.core.evaluator import Evaluator

EVALUATOR_REGISTRY: dict[str, type[Evaluator]] = {
    "exact_match": ExactMatchEvaluator,
    "rubric": RubricEvaluator,
    "llm_judge": LLMJudgeEvaluator,
    "composite": CompositeEvaluator,
}


def get_evaluator(name: str) -> Evaluator:
    try:
        cls = EVALUATOR_REGISTRY[name]
    except KeyError:
        available = ", ".join(sorted(EVALUATOR_REGISTRY))
        raise KeyError(
            f"Unknown evaluator {name!r}. Available evaluators: {available}"
        ) from None
    return cls()


def get_evaluator_registry() -> dict[str, Evaluator]:
    """Return a dict of instantiated evaluators keyed by name."""
    return {name: cls() for name, cls in EVALUATOR_REGISTRY.items()}
