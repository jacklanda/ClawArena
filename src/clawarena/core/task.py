from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class TaskCategory(str, enum.Enum):
    EMAIL = "email"
    SUMMARIZATION = "summarization"
    CASCADE = "cascade"
    GENERAL = "general"


class TaskDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ExecutionMode(str, enum.Enum):
    SANDBOXED = "sandboxed"
    REAL = "real"


@dataclass(frozen=True)
class EvaluationSpec:
    evaluator: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Task:
    id: str
    name: str
    category: TaskCategory
    difficulty: TaskDifficulty
    description: str
    instruction: str
    evaluation: EvaluationSpec
    context: dict[str, Any] = field(default_factory=dict)
    expected_output: Any = None
    timeout_seconds: int = 300
    execution_mode: ExecutionMode = ExecutionMode.SANDBOXED
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: Path | None = None


@dataclass
class TaskSuite:
    name: str
    description: str
    tasks: list[Task]

    @property
    def categories(self) -> set[TaskCategory]:
        return {t.category for t in self.tasks}

    def filter_by_category(self, category: TaskCategory) -> TaskSuite:
        return TaskSuite(
            name=f"{self.name}[{category.value}]",
            description=self.description,
            tasks=[t for t in self.tasks if t.category == category],
        )

    def filter_by_difficulty(self, difficulty: TaskDifficulty) -> TaskSuite:
        return TaskSuite(
            name=f"{self.name}[{difficulty.value}]",
            description=self.description,
            tasks=[t for t in self.tasks if t.difficulty == difficulty],
        )

    def __len__(self) -> int:
        return len(self.tasks)
