"""YAML task loader with Pydantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from clawarena.core.task import (
    EvaluationSpec,
    ExecutionMode,
    Task,
    TaskCategory,
    TaskDifficulty,
)


class EvaluationDefinition(BaseModel):
    """Pydantic model for the evaluation section of a task YAML."""

    evaluator: str
    config: dict[str, Any] = Field(default_factory=dict)


class TaskDefinition(BaseModel):
    """Pydantic model that validates a raw YAML task definition.

    After validation, use `to_task()` to convert into the core `Task` dataclass.
    """

    id: str
    name: str
    category: TaskCategory
    difficulty: TaskDifficulty
    description: str
    instruction: str
    evaluation: EvaluationDefinition
    context: dict[str, Any] = Field(default_factory=dict)
    expected_output: Any = None
    timeout_seconds: int = 300
    execution_mode: ExecutionMode = ExecutionMode.SANDBOXED
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Task id must not be empty")
        return v

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("timeout_seconds must be positive")
        return v

    def to_task(self, source_path: Path | None = None) -> Task:
        """Convert the validated Pydantic model into a core Task dataclass."""
        return Task(
            id=self.id,
            name=self.name,
            category=self.category,
            difficulty=self.difficulty,
            description=self.description,
            instruction=self.instruction,
            evaluation=EvaluationSpec(
                evaluator=self.evaluation.evaluator,
                config=self.evaluation.config,
            ),
            context=self.context,
            expected_output=self.expected_output,
            timeout_seconds=self.timeout_seconds,
            execution_mode=self.execution_mode,
            metadata=self.metadata,
            source_path=source_path,
        )


def load_task_from_yaml(path: Path) -> Task:
    """Load and validate a single task from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        A validated Task dataclass instance.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
        pydantic.ValidationError: If the data does not match the schema.
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a YAML mapping at top level in {path}")

    definition = TaskDefinition.model_validate(raw)
    return definition.to_task(source_path=path)


def load_tasks_from_directory(directory: Path) -> list[Task]:
    """Recursively discover and load all YAML task files from a directory.

    Args:
        directory: Root directory to scan for .yaml / .yml files.

    Returns:
        A list of validated Task instances, sorted by task id.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"Task directory not found: {directory}")

    tasks: list[Task] = []
    for yaml_path in sorted(directory.rglob("*.yaml")):
        tasks.append(load_task_from_yaml(yaml_path))
    for yml_path in sorted(directory.rglob("*.yml")):
        tasks.append(load_task_from_yaml(yml_path))

    tasks.sort(key=lambda t: t.id)
    return tasks
