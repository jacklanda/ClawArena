"""Task registry with discovery and filtering."""

from __future__ import annotations

from pathlib import Path

from clawarena.core.task import Task, TaskCategory, TaskDifficulty, TaskSuite
from clawarena.tasks.loader import load_tasks_from_directory

_BUILTIN_DIR = Path(__file__).parent / "builtin"


class TaskRegistry:
    """Central registry that discovers, stores, and queries tasks.

    Built-in tasks are loaded automatically from the ``builtin/`` directory
    that ships with the package.  Additional directories of custom tasks can
    be added at any time.
    """

    def __init__(self, *, load_builtin: bool = True) -> None:
        self._tasks: dict[str, Task] = {}
        self._directories: list[Path] = []

        if load_builtin and _BUILTIN_DIR.is_dir():
            self.add_directory(_BUILTIN_DIR)

    # -- mutation --------------------------------------------------------

    def add_directory(self, directory: Path) -> None:
        """Discover and register all tasks from a directory (recursive).

        Args:
            directory: Directory to scan for YAML task files.

        Raises:
            FileNotFoundError: If the directory does not exist.
            ValueError: If a duplicate task id is detected.
        """
        directory = Path(directory).resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"Task directory not found: {directory}")

        self._directories.append(directory)
        for task in load_tasks_from_directory(directory):
            if task.id in self._tasks:
                existing = self._tasks[task.id]
                raise ValueError(
                    f"Duplicate task id '{task.id}': "
                    f"already registered from {existing.source_path}, "
                    f"conflict with {task.source_path}"
                )
            self._tasks[task.id] = task

    def register(self, task: Task) -> None:
        """Register a single task programmatically.

        Args:
            task: The Task instance to register.

        Raises:
            ValueError: If a task with the same id is already registered.
        """
        if task.id in self._tasks:
            raise ValueError(f"Task '{task.id}' is already registered")
        self._tasks[task.id] = task

    # -- queries ---------------------------------------------------------

    def get(self, task_id: str) -> Task:
        """Return a task by its id.

        Raises:
            KeyError: If no task with the given id is registered.
        """
        try:
            return self._tasks[task_id]
        except KeyError:
            raise KeyError(f"No task registered with id '{task_id}'") from None

    def list_all(self) -> list[Task]:
        """Return all registered tasks sorted by id."""
        return sorted(self._tasks.values(), key=lambda t: t.id)

    def filter_by_category(self, category: TaskCategory) -> list[Task]:
        """Return tasks matching a specific category, sorted by id."""
        return sorted(
            (t for t in self._tasks.values() if t.category == category),
            key=lambda t: t.id,
        )

    def filter_by_difficulty(self, difficulty: TaskDifficulty) -> list[Task]:
        """Return tasks matching a specific difficulty, sorted by id."""
        return sorted(
            (t for t in self._tasks.values() if t.difficulty == difficulty),
            key=lambda t: t.id,
        )

    def as_suite(self, name: str = "default", description: str = "") -> TaskSuite:
        """Return all registered tasks wrapped in a TaskSuite."""
        return TaskSuite(
            name=name,
            description=description or f"All {len(self._tasks)} registered tasks",
            tasks=self.list_all(),
        )

    def __len__(self) -> int:
        return len(self._tasks)

    def __contains__(self, task_id: str) -> bool:
        return task_id in self._tasks
