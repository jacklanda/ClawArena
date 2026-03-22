from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from clawarena.core.task import Task


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


@dataclass(frozen=True)
class AgentInfo:
    name: str
    version: str
    model: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    output: Any
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    duration_seconds: float = 0.0
    api_calls: int = 0
    error: str | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class AgentAdapter(abc.ABC):
    @abc.abstractmethod
    def info(self) -> AgentInfo:
        ...

    @abc.abstractmethod
    async def run_task(self, task: Task) -> AgentResponse:
        ...

    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        pass
