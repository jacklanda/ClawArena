import pytest

from clawarena.adapters.builtin.dummy import DummyAdapter
from clawarena.core.task import (
    EvaluationSpec,
    Task,
    TaskCategory,
    TaskDifficulty,
    TaskSuite,
)
from clawarena.engine.pricing import PricingTable
from clawarena.engine.runner import RunConfig, RunEngine
from clawarena.evaluators import get_evaluator_registry


@pytest.fixture
def simple_suite():
    spec = EvaluationSpec(evaluator="exact_match", config={"contains": ["hello"]})
    task = Task(
        id="test/hello", name="Hello Test", category=TaskCategory.GENERAL,
        difficulty=TaskDifficulty.EASY, description="Say hello",
        instruction="Say hello", evaluation=spec,
        expected_output="hello world", timeout_seconds=10,
    )
    return TaskSuite(name="test", description="Test suite", tasks=[task])


@pytest.mark.asyncio
async def test_run_engine_basic(simple_suite):
    evaluator_reg = get_evaluator_registry()
    engine = RunEngine(evaluator_registry=evaluator_reg)
    adapter = DummyAdapter()

    results = await engine.run(simple_suite, [adapter])

    assert len(results) == 1
    run = results[0]
    assert run.agent.name == "DummyAgent"
    assert len(run.task_results) == 1
    assert run.completed_at is not None
    assert run.total_duration_seconds >= 0


@pytest.mark.asyncio
async def test_run_engine_cost_tracking(simple_suite):
    engine = RunEngine(
        evaluator_registry=get_evaluator_registry(),
        pricing=PricingTable(),
    )
    adapter = DummyAdapter()
    results = await engine.run(simple_suite, [adapter])
    run = results[0]

    # Dummy model has $0 pricing, so cost should be 0
    assert run.total_cost.total_cost_usd == 0.0
    assert run.total_tokens.total_tokens > 0
