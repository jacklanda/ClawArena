from __future__ import annotations

from dataclasses import dataclass

from clawarena.core.agent import TokenUsage
from clawarena.core.result import CostEstimate

# Pricing in USD per 1M tokens (input / output)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-opus-4-20250514": (15.0, 75.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-haiku-3.5": (0.80, 4.0),
    # OpenAI
    "gpt-4o": (2.50, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-4": (30.0, 60.0),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1": (15.0, 60.0),
    "o1-mini": (3.0, 12.0),
    "o3-mini": (1.10, 4.40),
    # Google
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-pro": (1.25, 10.0),
    "gemini-1.5-pro": (1.25, 5.0),
    "gemini-1.5-flash": (0.075, 0.30),
    # Meta / open source
    "llama-3.1-70b": (0.90, 0.90),
    "llama-3.1-8b": (0.20, 0.20),
    # Fallback
    "dummy-model": (0.0, 0.0),
    "unknown": (1.0, 1.0),
}


class PricingTable:
    def __init__(self, custom_pricing: dict[str, tuple[float, float]] | None = None) -> None:
        self._pricing = {**MODEL_PRICING}
        if custom_pricing:
            self._pricing.update(custom_pricing)

    def estimate(self, token_usage: TokenUsage, model: str) -> CostEstimate:
        input_price, output_price = self._pricing.get(
            model, self._pricing.get("unknown", (1.0, 1.0))
        )

        input_cost = (token_usage.input_tokens / 1_000_000) * input_price
        output_cost = (token_usage.output_tokens / 1_000_000) * output_price

        return CostEstimate(
            input_cost_usd=round(input_cost, 6),
            output_cost_usd=round(output_cost, 6),
            total_cost_usd=round(input_cost + output_cost, 6),
            pricing_model=model,
        )

    def list_models(self) -> list[str]:
        return sorted(self._pricing.keys())
