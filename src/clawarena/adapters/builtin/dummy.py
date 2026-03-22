from __future__ import annotations

import random
import time

from clawarena.core.agent import AgentAdapter, AgentInfo, AgentResponse, TokenUsage
from clawarena.core.task import Task


class DummyAdapter(AgentAdapter):
    """A dummy agent that returns canned responses. Used for testing the framework."""

    def __init__(self, **kwargs: object) -> None:
        self._call_count = 0

    def info(self) -> AgentInfo:
        return AgentInfo(
            name="DummyAgent",
            version="0.1.0",
            model="dummy-model",
            description="A dummy agent for testing ClawArena",
        )

    async def run_task(self, task: Task) -> AgentResponse:
        self._call_count += 1
        start = time.monotonic()

        output = self._generate_output(task)

        duration = time.monotonic() - start
        input_tokens = len(task.instruction.split()) * 2
        output_tokens = len(str(output).split()) * 2

        return AgentResponse(
            output=output,
            token_usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
            duration_seconds=duration,
            api_calls=1,
            trace=[{"step": "generate", "model": "dummy-model"}],
        )

    def _generate_output(self, task: Task) -> str:
        category = task.category.value

        if category == "email":
            return self._generate_email(task)
        elif category == "summarization":
            return self._generate_summary(task)
        elif category == "cascade":
            return self._generate_cascade(task)
        else:
            return self._generate_general(task)

    def _generate_email(self, task: Task) -> str:
        recipient = task.context.get("recipient", "user@example.com")
        subject = task.context.get("subject", "Update")
        key_points = task.context.get("key_points", [])
        tone = task.context.get("tone", "professional")

        points_text = "\n".join(f"- {p}" for p in key_points) if key_points else "No updates."

        return (
            f"To: {recipient}\n"
            f"Subject: {subject}\n\n"
            f"Dear colleague,\n\n"
            f"I wanted to share the following updates:\n\n"
            f"{points_text}\n\n"
            f"Please let me know if you have any questions.\n\n"
            f"Best regards,\n"
            f"DummyAgent"
        )

    def _generate_summary(self, task: Task) -> str:
        return (
            "## Summary\n\n"
            "Key highlights from the provided materials:\n\n"
            "1. Main topics were discussed and reviewed\n"
            "2. Action items were identified and assigned\n"
            "3. Follow-up meetings are scheduled\n\n"
            "### Action Items\n"
            "- Review pending items\n"
            "- Follow up on open questions\n"
        )

    def _generate_cascade(self, task: Task) -> str:
        return (
            "## Pipeline Results\n\n"
            "### Step 1: Data Extraction\n"
            "Extracted key metrics from the provided data.\n\n"
            "### Step 2: Analysis\n"
            "Analyzed trends and patterns.\n\n"
            "### Step 3: Output\n"
            "Generated final report with findings.\n"
        )

    def _generate_general(self, task: Task) -> str:
        return f"Task '{task.name}' completed successfully.\n\nOutput based on instruction:\n{task.instruction[:200]}"
