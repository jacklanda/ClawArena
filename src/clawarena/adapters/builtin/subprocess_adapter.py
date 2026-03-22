from __future__ import annotations

import asyncio
import json
import shlex
import tempfile
import time
from pathlib import Path
from typing import Any

from clawarena.core.agent import AgentAdapter, AgentInfo, AgentResponse, TokenUsage
from clawarena.core.task import Task


class SubprocessAdapter(AgentAdapter):
    """Run an external agent system as a subprocess.

    The command template supports placeholders:
    - {instruction}: The task instruction text
    - {context_file}: Path to a JSON file containing the task context
    - {task_id}: The task ID
    """

    def __init__(
        self,
        command: str,
        name: str = "SubprocessAgent",
        version: str = "0.0.0",
        model: str = "unknown",
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        self._command = command
        self._name = name
        self._version = version
        self._model = model
        self._cwd = cwd
        self._env = env

    def info(self) -> AgentInfo:
        return AgentInfo(
            name=self._name,
            version=self._version,
            model=self._model,
            description=f"Subprocess agent: {self._command}",
        )

    async def run_task(self, task: Task) -> AgentResponse:
        start = time.monotonic()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as ctx_file:
            json.dump(task.context, ctx_file)
            context_file_path = ctx_file.name

        try:
            cmd = self._command.format(
                instruction=shlex.quote(task.instruction),
                context_file=context_file_path,
                task_id=task.id,
            )

            import os

            env = {**os.environ, **(self._env or {})}

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._cwd,
                env=env,
            )
            stdout, stderr = await proc.communicate()
            duration = time.monotonic() - start

            output = stdout.decode("utf-8", errors="replace").strip()
            error = None
            if proc.returncode != 0:
                error = stderr.decode("utf-8", errors="replace").strip()

            return AgentResponse(
                output=output,
                duration_seconds=duration,
                api_calls=0,
                error=error,
                raw_metadata={
                    "returncode": proc.returncode,
                    "stderr": stderr.decode("utf-8", errors="replace"),
                },
            )

        finally:
            Path(context_file_path).unlink(missing_ok=True)
