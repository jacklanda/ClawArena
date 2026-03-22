from pathlib import Path

import pytest

from clawarena.tasks.loader import load_task_from_yaml, load_tasks_from_directory


BUILTIN_DIR = Path(__file__).parent.parent.parent / "src" / "clawarena" / "tasks" / "builtin"


def test_load_builtin_tasks():
    if not BUILTIN_DIR.is_dir():
        pytest.skip("Built-in task directory not found")
    tasks = load_tasks_from_directory(BUILTIN_DIR)
    assert len(tasks) == 10


def test_load_single_task():
    yaml_path = BUILTIN_DIR / "email" / "compose_simple.yaml"
    if not yaml_path.exists():
        pytest.skip("compose_simple.yaml not found")
    task = load_task_from_yaml(yaml_path)
    assert task.id == "email.compose_simple"
    assert task.category.value == "email"
    assert task.difficulty.value == "easy"


def test_load_nonexistent():
    with pytest.raises(FileNotFoundError):
        load_task_from_yaml(Path("/nonexistent/task.yaml"))


def test_registry():
    from clawarena.tasks.registry import TaskRegistry

    registry = TaskRegistry()
    tasks = registry.list_all()
    assert len(tasks) == 10

    email_tasks = registry.filter_by_category(
        __import__("clawarena.core.task", fromlist=["TaskCategory"]).TaskCategory.EMAIL
    )
    assert len(email_tasks) == 3

    suite = registry.as_suite("test")
    assert len(suite) == 10
