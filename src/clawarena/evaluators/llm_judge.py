"""LLM-as-a-judge evaluator with graceful dependency fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from clawarena.core.agent import AgentResponse
from clawarena.core.evaluator import Evaluator
from clawarena.core.result import TaskScore
from clawarena.core.task import Task

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default judge prompt
# ---------------------------------------------------------------------------

_DEFAULT_JUDGE_PROMPT = """\
You are an expert evaluator assessing an AI agent's response to a task.

## Task
{task_description}

## Instruction given to the agent
{task_instruction}

## Expected output (if available)
{expected_output}

## Agent's actual output
{agent_output}

## Scoring instructions
Rate the agent's output on four dimensions.  Each score MUST be a float
between 0.0 and 1.0 (inclusive).

1. **correctness** -- Does the output match the expected answer or fulfill
   the task requirement?
2. **completeness** -- Are all requested elements present?  Nothing missing?
3. **efficiency** -- Is the output concise without unnecessary verbosity?
4. **robustness** -- Is the output well-formed and free of errors or
   hallucinated content?

Return **only** a JSON object with exactly these keys:
```json
{{
    "correctness": <float>,
    "completeness": <float>,
    "efficiency": <float>,
    "robustness": <float>,
    "reasoning": "<brief explanation>"
}}
```
"""


class LLMJudgeEvaluator(Evaluator):
    """Uses an LLM to judge the quality of an agent response.

    The evaluator attempts to call an LLM (OpenAI or Anthropic) to produce
    structured scores.  If the required client library is not installed, or
    the API call fails, it falls back to a basic heuristic scorer so that
    evaluation runs are never blocked by infrastructure issues.

    Config keys
    -----------
    judge_model : str
        The model identifier to use (default ``"gpt-4o"``).
    judge_prompt : str, optional
        A custom prompt template.  The following placeholders are available:
        ``{task_description}``, ``{task_instruction}``, ``{expected_output}``,
        ``{agent_output}``.
    provider : str
        ``"openai"`` (default) or ``"anthropic"``.
    api_key : str, optional
        Explicit API key.  When omitted the client library's default
        environment-variable lookup is used.
    temperature : float
        Sampling temperature for the judge call (default ``0.0``).
    """

    @property
    def name(self) -> str:
        return "llm_judge"

    async def evaluate(
        self,
        task: Task,
        response: AgentResponse,
        config: dict[str, Any] | None = None,
    ) -> TaskScore:
        config = config or {}
        provider: str = config.get("provider", "openai")
        judge_model: str = config.get("judge_model", "gpt-4o")
        temperature: float = float(config.get("temperature", 0.0))
        judge_prompt: str = config.get("judge_prompt", _DEFAULT_JUDGE_PROMPT)

        prompt = judge_prompt.format(
            task_description=task.description,
            task_instruction=task.instruction,
            expected_output=task.expected_output or "(not provided)",
            agent_output=_to_str(response.output),
        )

        scores: dict[str, Any] | None = None

        if provider == "openai":
            scores = await _call_openai(prompt, judge_model, temperature, config)
        elif provider == "anthropic":
            scores = await _call_anthropic(prompt, judge_model, temperature, config)
        else:
            logger.warning("Unknown LLM judge provider %r; falling back to heuristic.", provider)

        if scores is None:
            logger.info("LLM judge unavailable; using heuristic fallback.")
            return _heuristic_fallback(task, response)

        correctness = _clamp(scores.get("correctness", 0.0))
        completeness = _clamp(scores.get("completeness", 0.0))
        efficiency = _clamp(scores.get("efficiency", 0.0))
        robustness = _clamp(scores.get("robustness", 0.0))
        reasoning: str = scores.get("reasoning", "")

        overall = (
            0.40 * correctness
            + 0.25 * completeness
            + 0.15 * efficiency
            + 0.20 * robustness
        )

        return TaskScore(
            correctness=round(correctness, 4),
            completeness=round(completeness, 4),
            efficiency=round(efficiency, 4),
            robustness=round(robustness, 4),
            overall=round(overall, 4),
            evaluator_details={
                "evaluator": self.name,
                "judge_model": judge_model,
                "provider": provider,
                "reasoning": reasoning,
                "fallback_used": False,
            },
        )


# ---------------------------------------------------------------------------
# LLM client helpers
# ---------------------------------------------------------------------------

async def _call_openai(
    prompt: str,
    model: str,
    temperature: float,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    """Attempt to score via OpenAI.  Returns *None* on any failure."""
    try:
        import openai  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("openai package not installed.")
        return None

    try:
        api_key: str | None = config.get("api_key")
        client_kwargs: dict[str, Any] = {}
        if api_key:
            client_kwargs["api_key"] = api_key

        client = openai.AsyncOpenAI(**client_kwargs)
        chat_response = await client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        content = chat_response.choices[0].message.content or ""
        return _parse_json_scores(content)
    except Exception:
        logger.exception("OpenAI judge call failed.")
        return None


async def _call_anthropic(
    prompt: str,
    model: str,
    temperature: float,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    """Attempt to score via Anthropic.  Returns *None* on any failure."""
    try:
        import anthropic  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("anthropic package not installed.")
        return None

    try:
        api_key: str | None = config.get("api_key")
        client_kwargs: dict[str, Any] = {}
        if api_key:
            client_kwargs["api_key"] = api_key

        client = anthropic.AsyncAnthropic(**client_kwargs)
        message = await client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text if message.content else ""
        return _parse_json_scores(content)
    except Exception:
        logger.exception("Anthropic judge call failed.")
        return None


# ---------------------------------------------------------------------------
# Parsing & fallback helpers
# ---------------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_BARE_JSON_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_json_scores(text: str) -> dict[str, Any] | None:
    """Best-effort extraction of a JSON object from LLM output."""
    # Try fenced code block first
    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Try bare JSON
    m = _BARE_JSON_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # Last resort: the whole string
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Could not parse JSON from LLM judge response.")
        return None


def _clamp(value: Any, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a numeric value to ``[lo, hi]``."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(lo, min(hi, f))


def _to_str(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _heuristic_fallback(task: Task, response: AgentResponse) -> TaskScore:
    """Very simple length/keyword heuristic used when no LLM is available."""
    output = _to_str(response.output)
    expected = _to_str(task.expected_output) if task.expected_output is not None else None

    # Correctness: crude token overlap
    if expected:
        expected_tokens = set(expected.lower().split())
        output_tokens = set(output.lower().split())
        if expected_tokens:
            overlap = len(expected_tokens & output_tokens) / len(expected_tokens)
            correctness = min(overlap, 1.0)
        else:
            correctness = 0.5
    else:
        correctness = 0.5 if output.strip() else 0.0

    # Completeness: non-empty output is considered at least partially complete
    completeness = 1.0 if len(output.strip()) > 20 else (0.5 if output.strip() else 0.0)

    # Efficiency
    if expected and len(expected) > 0:
        ratio = len(output) / max(len(expected), 1)
        if ratio <= 2.0:
            efficiency = 1.0
        elif ratio >= 5.0:
            efficiency = 0.2
        else:
            efficiency = 1.0 - 0.8 * (ratio - 2.0) / 3.0
    else:
        efficiency = 1.0 if len(output) <= 500 else 0.6

    # Robustness
    robustness = 1.0 if response.error is None else 0.0

    overall = (
        0.40 * correctness
        + 0.25 * completeness
        + 0.15 * efficiency
        + 0.20 * robustness
    )

    return TaskScore(
        correctness=round(correctness, 4),
        completeness=round(completeness, 4),
        efficiency=round(efficiency, 4),
        robustness=round(robustness, 4),
        overall=round(overall, 4),
        evaluator_details={
            "evaluator": "llm_judge",
            "fallback_used": True,
            "reasoning": "LLM judge unavailable; scored with token-overlap heuristic.",
        },
    )
