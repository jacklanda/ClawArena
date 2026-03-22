from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from clawarena.core.task import Task


class Sandbox:
    """Per-task sandboxing: creates a temporary directory, provisions fixtures, and cleans up."""

    def __init__(self, task: Task, base_dir: Path | None = None) -> None:
        self._task = task
        self._base_dir = base_dir
        self._tmp_dir: Path | None = None

    @property
    def work_dir(self) -> Path:
        if self._tmp_dir is None:
            raise RuntimeError("Sandbox not provisioned. Use `async with Sandbox(task):`")
        return self._tmp_dir

    async def provision(self) -> Path:
        self._tmp_dir = Path(
            tempfile.mkdtemp(
                prefix=f"clawarena_{self._task.id.replace('/', '_')}_",
                dir=self._base_dir,
            )
        )

        fixtures = self._task.context.get("fixtures", [])
        for fixture in fixtures:
            src = Path(fixture["source"])
            dst = self._tmp_dir / fixture["destination"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.exists():
                shutil.copy2(src, dst)

        return self._tmp_dir

    async def cleanup(self) -> None:
        if self._tmp_dir and self._tmp_dir.exists():
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
            self._tmp_dir = None

    async def __aenter__(self) -> Sandbox:
        await self.provision()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.cleanup()
