import pytest

from clawarena.evaluators.exact_match import ExactMatchEvaluator
from clawarena.evaluators.rubric import RubricEvaluator
from clawarena.core.agent import AgentResponse, TokenUsage
from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec


@pytest.fixture
def email_task():
    return Task(
        id="test/email", name="Test Email", category=TaskCategory.EMAIL,
        difficulty=TaskDifficulty.EASY, description="Write an email",
        instruction="Write an email to Bob",
        evaluation=EvaluationSpec(evaluator="exact_match"),
        expected_output="Hello Bob, this is a test email.",
    )


@pytest.fixture
def good_response():
    return AgentResponse(
        output="Hello Bob, this is a test email.",
        token_usage=TokenUsage(input_tokens=50, output_tokens=20, total_tokens=70),
        duration_seconds=0.5,
    )


@pytest.fixture
def partial_response():
    return AgentResponse(
        output="Hello Bob, here is some info.",
        token_usage=TokenUsage(input_tokens=50, output_tokens=20, total_tokens=70),
        duration_seconds=0.5,
    )


@pytest.mark.asyncio
async def test_exact_match_perfect(email_task, good_response):
    evaluator = ExactMatchEvaluator()
    score = await evaluator.evaluate(email_task, good_response)
    assert score.correctness == 1.0
    assert score.robustness == 1.0
    assert score.overall > 0.8


@pytest.mark.asyncio
async def test_exact_match_partial(email_task, partial_response):
    evaluator = ExactMatchEvaluator()
    score = await evaluator.evaluate(email_task, partial_response)
    assert 0.0 < score.correctness < 1.0


@pytest.mark.asyncio
async def test_exact_match_contains(email_task, good_response):
    evaluator = ExactMatchEvaluator()
    config = {"contains": ["Hello", "Bob"], "case_sensitive": True}
    score = await evaluator.evaluate(email_task, good_response, config)
    assert score.completeness == 1.0


@pytest.mark.asyncio
async def test_rubric_evaluator():
    task = Task(
        id="test/rubric", name="Test", category=TaskCategory.GENERAL,
        difficulty=TaskDifficulty.EASY, description="Greet the user",
        instruction="Say hello",
        evaluation=EvaluationSpec(evaluator="rubric"),
    )
    response = AgentResponse(
        output="Hello! Welcome to our service. We are glad to have you.",
        token_usage=TokenUsage(input_tokens=20, output_tokens=15, total_tokens=35),
        duration_seconds=0.3,
    )
    evaluator = RubricEvaluator()
    config = {
        "criteria": [
            {"name": "greeting", "description": "Contains a greeting", "weight": 1.0,
             "keywords": ["hello", "welcome"]},
            {"name": "positive", "description": "Positive tone", "weight": 1.0,
             "keywords": ["glad", "happy", "pleased"]},
        ],
        "pass_threshold": 0.5,
    }
    score = await evaluator.evaluate(task, response, config)
    assert score.correctness > 0.5
    assert score.robustness == 1.0
