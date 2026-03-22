import pytest


@pytest.fixture
def sample_task():
    from clawarena.core.task import (
        EvaluationSpec,
        ExecutionMode,
        Task,
        TaskCategory,
        TaskDifficulty,
    )

    return Task(
        id="test/sample",
        name="Sample Task",
        category=TaskCategory.GENERAL,
        difficulty=TaskDifficulty.EASY,
        description="A test task",
        instruction="Do the thing",
        evaluation=EvaluationSpec(evaluator="exact_match", config={}),
        context={"key": "value"},
        expected_output="expected result",
        timeout_seconds=30,
        execution_mode=ExecutionMode.SANDBOXED,
    )


@pytest.fixture
def sample_response():
    from clawarena.core.agent import AgentResponse, TokenUsage

    return AgentResponse(
        output="expected result",
        token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        duration_seconds=1.5,
        api_calls=1,
    )
