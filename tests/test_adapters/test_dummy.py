import pytest

from clawarena.adapters.builtin.dummy import DummyAdapter
from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec


@pytest.fixture
def dummy_adapter():
    return DummyAdapter()


@pytest.fixture
def email_task():
    return Task(
        id="test/email", name="Test Email", category=TaskCategory.EMAIL,
        difficulty=TaskDifficulty.EASY, description="Compose email",
        instruction="Write an email",
        evaluation=EvaluationSpec(evaluator="rubric"),
        context={"recipient": "bob@test.com", "subject": "Test", "key_points": ["point 1"]},
    )


def test_dummy_info(dummy_adapter):
    info = dummy_adapter.info()
    assert info.name == "DummyAgent"
    assert info.model == "dummy-model"


@pytest.mark.asyncio
async def test_dummy_run_email(dummy_adapter, email_task):
    response = await dummy_adapter.run_task(email_task)
    assert response.output is not None
    assert "bob@test.com" in response.output
    assert response.token_usage.total_tokens > 0
    assert response.api_calls == 1
    assert response.error is None


@pytest.mark.asyncio
async def test_dummy_run_general(dummy_adapter):
    task = Task(
        id="test/gen", name="General Task", category=TaskCategory.GENERAL,
        difficulty=TaskDifficulty.EASY, description="Do something",
        instruction="Just do it",
        evaluation=EvaluationSpec(evaluator="exact_match"),
    )
    response = await dummy_adapter.run_task(task)
    assert response.output is not None
    assert response.error is None
