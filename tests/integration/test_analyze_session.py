"""Integration tests for session analysis."""

import os
import tempfile

from src.copilot_usage_analyser.application.use_cases import AnalyzeSession, GenerateReport, ReportConfig
from src.copilot_usage_analyser.domain.services import CostCalculator, HotspotDetector, MetricsCalculator
from src.copilot_usage_analyser.domain.value_objects import PricingConfig
from src.copilot_usage_analyser.infrastructure.adapters import ChatReplayAdapter, CopilotOTelAdapter
from src.copilot_usage_analyser.infrastructure.charts import ChartGenerator
from src.copilot_usage_analyser.infrastructure.readers import LogFileReader


def _make_analyze_use_case():
    pricing_config = PricingConfig(
        plan_type="business",
        included_credits_per_month=1900,
        credit_to_usd_rate=0.01,
    )
    return AnalyzeSession(
        file_reader=LogFileReader(),
        chatreplay_adapter=ChatReplayAdapter(),
        copilot_otel_adapter=CopilotOTelAdapter(),
        metrics_calculator=MetricsCalculator(),
        cost_calculator=CostCalculator(pricing_config),
        hotspot_detector=HotspotDetector(),
    )


def test_analyze_session_integration():
    """Test end-to-end session analysis with Copilot CLI OTel JSONL fixture."""
    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "sample_logs", "simple_session.jsonl"
    )

    result = _make_analyze_use_case().execute(fixture_path)

    assert result.session is not None
    assert result.metrics.total_events == 3   # invoke_agent + chat + execute_tool
    assert result.metrics.model_turns == 1    # one chat span
    assert result.metrics.tool_calls == 1     # one execute_tool span
    assert result.metrics.total_tokens_input == 100
    assert result.metrics.total_tokens_output == 50
    assert result.total_cost_usd >= 0
    assert result.total_credits >= 0


def test_generate_report_integration():
    """Test end-to-end report generation with Copilot CLI OTel JSONL fixture."""
    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "sample_logs", "simple_session.jsonl"
    )

    result = _make_analyze_use_case().execute(fixture_path)

    # Generate report
    with tempfile.TemporaryDirectory() as temp_dir:
        chart_generator = ChartGenerator(temp_dir)
        report_config = ReportConfig(
            report_type="detailed",
            include_charts=True,
            chart_format="png",
            output_format="markdown",
        )

        generate_use_case = GenerateReport(chart_generator=chart_generator)
        report = generate_use_case.execute(
            session=result.session,
            metrics=result.metrics,
            model_usage=result.model_usage,
            tool_usage=result.tool_usage,
            hotspots=result.hotspots,
            total_cost_usd=result.total_cost_usd,
            total_credits=result.total_credits,
            config=report_config,
        )

        # Verify report
        assert report is not None
        assert "Copilot Usage Analysis Report" in report
        assert "## Executive Summary" in report
        assert "## Session Overview" in report
        assert "## Token Analysis" in report
