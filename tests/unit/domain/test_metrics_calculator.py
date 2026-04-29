"""Unit tests for MetricsCalculator."""

from src.copilot_usage_analyser.domain.services import MetricsCalculator


def test_calculate_session_metrics(sample_events, sample_session):
    """Test calculation of session metrics."""
    calculator = MetricsCalculator()
    metrics = calculator.calculate_session_metrics(sample_events, sample_session)

    assert metrics.total_events == 3
    assert metrics.model_turns == 2
    assert metrics.tool_calls == 1
    assert metrics.total_tokens_input == 5100
    assert metrics.total_tokens_output == 2050
    assert metrics.total_tokens_cached == 100
    assert metrics.errors == 0


def test_calculate_token_usage_by_model(sample_events):
    """Test calculation of token usage by model."""
    calculator = MetricsCalculator()
    model_usage = calculator.calculate_token_usage_by_model(sample_events)

    assert len(model_usage) == 1
    assert model_usage[0].model_name == "gpt-4"
    assert model_usage[0].provider == "openai"
    assert model_usage[0].total_input_tokens == 5100
    assert model_usage[0].total_output_tokens == 2050
    assert model_usage[0].total_cached_tokens == 100
    assert model_usage[0].total_requests == 2


def test_calculate_tool_usage(sample_events):
    """Test calculation of tool usage statistics."""
    calculator = MetricsCalculator()
    tool_usage = calculator.calculate_tool_usage(sample_events)

    assert len(tool_usage) == 1
    assert tool_usage[0].tool_name == "read_file"
    assert tool_usage[0].invocation_count == 1
    assert tool_usage[0].success_count == 1
    assert tool_usage[0].failure_count == 0
