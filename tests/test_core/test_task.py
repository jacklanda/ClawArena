from clawarena.core.task import (
    EvaluationSpec,
    ExecutionMode,
    Task,
    TaskCategory,
    TaskDifficulty,
    TaskSuite,
)


def test_task_creation(sample_task):
    assert sample_task.id == "test/sample"
    assert sample_task.category == TaskCategory.GENERAL
    assert sample_task.difficulty == TaskDifficulty.EASY
    assert sample_task.execution_mode == ExecutionMode.SANDBOXED


def test_task_suite_filter():
    spec = EvaluationSpec(evaluator="exact_match")
    tasks = [
        Task(id="a", name="A", category=TaskCategory.EMAIL, difficulty=TaskDifficulty.EASY,
             description="", instruction="", evaluation=spec),
        Task(id="b", name="B", category=TaskCategory.EMAIL, difficulty=TaskDifficulty.HARD,
             description="", instruction="", evaluation=spec),
        Task(id="c", name="C", category=TaskCategory.GENERAL, difficulty=TaskDifficulty.EASY,
             description="", instruction="", evaluation=spec),
    ]
    suite = TaskSuite(name="test", description="", tasks=tasks)

    email_suite = suite.filter_by_category(TaskCategory.EMAIL)
    assert len(email_suite) == 2

    easy_suite = suite.filter_by_difficulty(TaskDifficulty.EASY)
    assert len(easy_suite) == 2

    assert suite.categories == {TaskCategory.EMAIL, TaskCategory.GENERAL}


def test_evaluation_spec():
    spec = EvaluationSpec(evaluator="rubric", config={"pass_threshold": 0.8})
    assert spec.evaluator == "rubric"
    assert spec.config["pass_threshold"] == 0.8
