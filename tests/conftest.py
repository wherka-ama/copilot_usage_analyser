"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.copilot_usage_analyser.domain.entities import (
    AgentType,
    Event,
    EventType,
    PlanType,
    Session,
    TokenUsage,
)
from src.copilot_usage_analyser.domain.value_objects import ModelPricing, PricingConfig


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return Session(
        session_id=uuid4(),
        title="Test Session",
        start_time=datetime.utcnow() - timedelta(minutes=10),
        end_time=datetime.utcnow(),
        agent_type=AgentType.VSCODE,
        model="gpt-4",
        plan_type=PlanType.BUSINESS,
    )


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    base_time = datetime.utcnow() - timedelta(minutes=10)
    events = []

    # Model turn
    events.append(
        Event(
            event_id=uuid4(),
            timestamp=base_time,
            event_type=EventType.MODEL_TURN,
            summary="Initial request",
            token_usage=TokenUsage(input=100, output=50, cached=0),
            duration_ms=2000,
            details={"model": "gpt-4", "provider": "openai"},
        )
    )

    # Tool call
    events.append(
        Event(
            event_id=uuid4(),
            timestamp=base_time + timedelta(seconds=3),
            event_type=EventType.TOOL_CALL,
            summary="Read file",
            token_usage=TokenUsage(input=0, output=0, cached=0),
            duration_ms=100,
            details={"tool_name": "read_file"},
        )
    )

    # Another model turn with high token usage
    events.append(
        Event(
            event_id=uuid4(),
            timestamp=base_time + timedelta(seconds=5),
            event_type=EventType.MODEL_TURN,
            summary="Generate code",
            token_usage=TokenUsage(input=5000, output=2000, cached=100),
            duration_ms=15000,
            details={"model": "gpt-4", "provider": "openai"},
        )
    )

    return events


@pytest.fixture
def sample_pricing_config():
    """Create a sample pricing configuration."""
    return PricingConfig(
        plan_type="business",
        included_credits_per_month=1900,
        credit_to_usd_rate=0.01,
        model_pricing={
            "openai": {
                "gpt-4": ModelPricing(
                    input_per_million=30,
                    output_per_million=60,
                    cached_read_per_million=0.1,
                    cached_write_per_million=30,
                )
            }
        },
    )
