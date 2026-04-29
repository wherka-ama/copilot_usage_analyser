"""Pricing configuration value objects."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ModelPricing:
    """Pricing for a specific model."""

    input_per_million: float
    output_per_million: float
    cached_read_per_million: float = 0.0
    cached_write_per_million: float = 0.0


@dataclass(frozen=True)
class PricingConfig:
    """Configuration for pricing calculations."""

    plan_type: str
    included_credits_per_month: int
    credit_to_usd_rate: float
    model_pricing: Dict[str, Dict[str, ModelPricing]] = field(default_factory=dict)
