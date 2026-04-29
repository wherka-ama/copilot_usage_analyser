"""Unit tests for CostCalculator."""

from src.copilot_usage_analyser.domain.services import CostCalculator


def test_calculate_event_cost(sample_events, sample_pricing_config):
    """Test cost calculation for a single event."""
    calculator = CostCalculator(sample_pricing_config)
    event = sample_events[2]  # The high token usage event

    cost = calculator.calculate_event_cost(event)

    # Expected: (5000/1M * 30) + (2000/1M * 60) + (100/1M * 0.1) + (100/1M * 30)
    # = 0.15 + 0.12 + 0.00001 + 0.003 = 0.27301
    expected_cost = (5000 / 1_000_000) * 30 + (2000 / 1_000_000) * 60
    assert abs(cost - expected_cost) < 0.001


def test_calculate_session_cost(sample_events, sample_pricing_config):
    """Test cost calculation for a session."""
    calculator = CostCalculator(sample_pricing_config)
    cost = calculator.calculate_session_cost(sample_events)

    assert cost > 0
    assert cost < 1.0  # Should be less than $1 for this sample


def test_calculate_credits(sample_pricing_config):
    """Test credit calculation."""
    calculator = CostCalculator(sample_pricing_config)

    credits = calculator.calculate_credits(0.50)
    assert credits == 50  # 0.50 USD / 0.01 = 50 credits

    credits = calculator.calculate_credits(1.23)
    assert credits == 123
