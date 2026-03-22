"""Abstract base class for all ClawArena evaluators."""

from __future__ import annotations

import abc
from typing import Any

from clawarena.core.agent import AgentResponse
from clawarena.core.result import TaskScore
from clawarena.core.task import Task


class Evaluator(abc.ABC):
    """Base class that every evaluator must implement.

    An evaluator inspects the agent's response for a given task and produces
    a :class:`TaskScore` with dimension-level scores (correctness,
    completeness, efficiency, robustness) and an overall score.
    """

    @abc.abstractmethod
    async def evaluate(
        self,
        task: Task,
        response: AgentResponse,
        config: dict[str, Any] | None = None,
    ) -> TaskScore:
        """Score *response* against *task*.

        Parameters
        ----------
        task:
            The task definition that was given to the agent.
        response:
            The agent's response to the task.
        config:
            Optional evaluator-specific configuration that may override
            defaults set at construction time.

        Returns
        -------
        TaskScore
            A dataclass containing per-dimension scores and an overall score.
        """
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """A short, unique identifier for this evaluator (e.g. ``"exact_match"``)."""
        ...
