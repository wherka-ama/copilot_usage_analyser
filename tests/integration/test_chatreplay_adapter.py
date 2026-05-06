"""Integration tests for ChatReplay adapter."""

import os

from src.copilot_usage_analyser.application.use_cases import AnalyzeSession, GenerateReport, ReportConfig
from src.copilot_usage_analyser.domain.services import CostCalculator, HotspotDetector, MetricsCalculator
from src.copilot_usage_analyser.domain.value_objects import PricingConfig
from src.copilot_usage_analyser.infrastructure.adapters import ChatReplayAdapter, CopilotOTelAdapter
from src.copilot_usage_analyser.infrastructure.charts import ChartGenerator
from src.copilot_usage_analyser.infrastructure.readers import LogFileReader


def test_chatreplay_adapter_integration():
    """Test ChatReplay adapter with real log sample."""
    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "sample_logs", "sample_chatreplay.json"
    )

    # Initialize components
    file_reader = LogFileReader()
    chatreplay_adapter = ChatReplayAdapter()

    # Read and detect format
    format_type = file_reader.detect_format(fixture_path)
    assert format_type == "chatreplay"

    # Read file
    raw_data = file_reader.read_file(fixture_path)

    # Adapt format
    session, events = chatreplay_adapter.adapt(raw_data)

    # Verify session
    assert session is not None
    assert session.agent_type.value == "vscode"
    assert session.plan_type.value == "business"

    # Verify events were extracted
    assert len(events) > 0


def test_analyze_chatreplay_session():
    """Test end-to-end analysis with ChatReplay format."""
    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "sample_logs", "sample_chatreplay.json"
    )

    # Initialize components
    file_reader = LogFileReader()
    pricing_config = PricingConfig(
        plan_type="business",
        included_credits_per_month=1900,
        credit_to_usd_rate=0.01,
    )
    cost_calculator = CostCalculator(pricing_config)

    # Create use case
    analyze_use_case = AnalyzeSession(
        file_reader=file_reader,
        chatreplay_adapter=ChatReplayAdapter(),
        copilot_otel_adapter=CopilotOTelAdapter(),
        metrics_calculator=MetricsCalculator(),
        cost_calculator=cost_calculator,
        hotspot_detector=HotspotDetector(),
    )

    # Execute
    result = analyze_use_case.execute(fixture_path)

    # Verify results
    assert result.session is not None
    assert result.metrics.total_events > 0
    assert result.total_cost_usd >= 0
    assert result.total_credits >= 0


def test_generate_report_from_chatreplay():
    """Test report generation from ChatReplay data."""
    import tempfile

    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "sample_logs", "sample_chatreplay.json"
    )

    # Analyze session first
    file_reader = LogFileReader()
    pricing_config = PricingConfig(
        plan_type="business",
        included_credits_per_month=1900,
        credit_to_usd_rate=0.01,
    )
    cost_calculator = CostCalculator(pricing_config)

    analyze_use_case = AnalyzeSession(
        file_reader=file_reader,
        chatreplay_adapter=ChatReplayAdapter(),
        copilot_otel_adapter=CopilotOTelAdapter(),
        metrics_calculator=MetricsCalculator(),
        cost_calculator=cost_calculator,
        hotspot_detector=HotspotDetector(),
    )

    result = analyze_use_case.execute(fixture_path)

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
