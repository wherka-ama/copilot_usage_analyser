"""Pricing configuration loader from YAML files."""

import os
from pathlib import Path
from typing import Dict, Optional

import yaml

from copilot_usage_analyser.domain.value_objects import ModelPricing, PricingConfig


class PricingConfigLoader:
    """Load pricing configuration from YAML files."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize with optional custom config directory."""
        if config_dir is None:
            # Try multiple locations for config directory
            possible_locations = [
                # Inside package (if installed with package data)
                Path(__file__).parent.parent.parent / "config" / "pricing",
                # Source directory (development mode)
                Path(__file__).parent.parent.parent.parent.parent / "config" / "pricing",
                # Relative to current working directory
                Path.cwd() / "config" / "pricing",
            ]
            
            for location in possible_locations:
                if location.exists():
                    config_dir = location
                    break
            
            if config_dir is None:
                # Fallback to first location (will raise error if not found)
                config_dir = possible_locations[0]
                
        self.config_dir = config_dir

    def load(self, plan_type: str = "business") -> PricingConfig:
        """Load pricing configuration for a specific plan type."""
        config_file = self.config_dir / f"{plan_type}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Pricing configuration file not found: {config_file}"
            )
        
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)
        
        return self._parse_config(config_data)
    
    def _parse_config(self, config_data: Dict) -> PricingConfig:
        """Parse YAML config data into PricingConfig object."""
        plan_type = config_data.get("plan_type", "business")
        included_credits = config_data.get("included_credits_per_month", 1900)
        credit_rate = config_data.get("credit_to_usd_rate", 0.01)
        
        model_pricing_data = config_data.get("model_pricing", {})
        model_pricing = self._parse_model_pricing(model_pricing_data)
        
        return PricingConfig(
            plan_type=plan_type,
            included_credits_per_month=included_credits,
            credit_to_usd_rate=credit_rate,
            model_pricing=model_pricing,
        )
    
    def _parse_model_pricing(self, model_pricing_data: Dict) -> Dict[str, Dict[str, ModelPricing]]:
        """Parse model pricing data from YAML."""
        model_pricing = {}
        
        for provider, models in model_pricing_data.items():
            provider_pricing = {}
            for model_name, pricing_data in models.items():
                provider_pricing[model_name] = ModelPricing(
                    input_per_million=pricing_data.get("input_per_million", 0.0),
                    output_per_million=pricing_data.get("output_per_million", 0.0),
                    cached_read_per_million=pricing_data.get("cached_read_per_million", 0.0),
                    cached_write_per_million=pricing_data.get("cached_write_per_million", 0.0),
                )
            model_pricing[provider] = provider_pricing
        
        return model_pricing
