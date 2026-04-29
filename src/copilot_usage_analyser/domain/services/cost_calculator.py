"""Cost calculator service."""

from typing import List

from ..entities import Event, ModelTokenUsage, Session
from ..value_objects import PricingConfig


class CostCalculator:
    """Service for calculating costs based on token usage."""

    def __init__(self, pricing_config: PricingConfig):
        """Initialize with pricing configuration."""
        self.pricing = pricing_config

    def calculate_event_cost(self, event: Event) -> float:
        """Calculate cost for a single event."""
        model = event.details.get("model", "gpt-4") if event.details else "gpt-4"
        provider = event.details.get("provider", "openai") if event.details else "openai"

        model_pricing = self._get_model_pricing(provider, model)
        if not model_pricing:
            return 0.0

        input_cost = (event.token_usage.input / 1_000_000) * model_pricing.input_per_million
        output_cost = (event.token_usage.output / 1_000_000) * model_pricing.output_per_million
        cached_read_cost = (
            (event.token_usage.cached / 1_000_000) * model_pricing.cached_read_per_million
        )
        cached_write_cost = (
            (event.token_usage.cached / 1_000_000) * model_pricing.cached_write_per_million
        )

        return input_cost + output_cost + cached_read_cost + cached_write_cost

    def calculate_session_cost(self, events: List[Event]) -> float:
        """Calculate total cost for a session."""
        return sum(self.calculate_event_cost(event) for event in events)

    def calculate_credits(self, cost_usd: float) -> int:
        """Convert USD to AI credits."""
        return int(cost_usd / self.pricing.credit_to_usd_rate)

    def update_model_costs(self, model_usages: List[ModelTokenUsage]) -> List[ModelTokenUsage]:
        """Update cost estimates for model usage list."""
        updated = []
        for usage in model_usages:
            model_pricing = self._get_model_pricing(usage.provider, usage.model_name)
            if model_pricing:
                input_cost = (usage.total_input_tokens / 1_000_000) * model_pricing.input_per_million
                output_cost = (
                    (usage.total_output_tokens / 1_000_000) * model_pricing.output_per_million
                )
                cached_read_cost = (
                    (usage.total_cached_tokens / 1_000_000) * model_pricing.cached_read_per_million
                )
                cached_write_cost = (
                    (usage.total_cached_tokens / 1_000_000) * model_pricing.cached_write_per_million
                )
                total_cost = input_cost + output_cost + cached_read_cost + cached_write_cost

                updated.append(
                    ModelTokenUsage(
                        model_name=usage.model_name,
                        provider=usage.provider,
                        total_input_tokens=usage.total_input_tokens,
                        total_output_tokens=usage.total_output_tokens,
                        total_cached_tokens=usage.total_cached_tokens,
                        total_requests=usage.total_requests,
                        estimated_cost_usd=total_cost,
                    )
                )
            else:
                updated.append(usage)
        return updated

    def _get_model_pricing(self, provider: str, model: str):
        """Get pricing for a specific model."""
        provider_pricing = self.pricing.model_pricing.get(provider, {})
        return provider_pricing.get(model)
