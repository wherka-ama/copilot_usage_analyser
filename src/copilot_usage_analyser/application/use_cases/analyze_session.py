"""Use case for analyzing a Copilot session."""

from dataclasses import dataclass, field
from typing import List, Optional

from ...domain.entities import ContextOverheadStats, Hotspot, ModelTokenUsage, Session, SessionMetrics, ToolUsageStats
from ...domain.services import CostCalculator, HotspotDetector, MetricsCalculator
from ...infrastructure.adapters import ChatReplayAdapter, CopilotOTelAdapter, OTLPAdapter
from ...infrastructure.readers import LogFileReader


@dataclass
class ParsedSession:
    """Result of parsing and analyzing a session."""

    session: Session
    events: List
    metrics: SessionMetrics
    model_usage: List[ModelTokenUsage]
    tool_usage: List[ToolUsageStats]
    hotspots: List[Hotspot]
    total_cost_usd: float
    total_credits: int
    context_overhead: Optional[ContextOverheadStats] = None


class AnalyzeSession:
    """Use case for analyzing a Copilot session log file."""

    def __init__(
        self,
        file_reader: LogFileReader,
        chatreplay_adapter: ChatReplayAdapter,
        otlp_adapter: OTLPAdapter,
        metrics_calculator: MetricsCalculator,
        cost_calculator: CostCalculator,
        hotspot_detector: HotspotDetector,
        copilot_otel_adapter: Optional[CopilotOTelAdapter] = None,
    ):
        """Initialize with dependencies."""
        self.file_reader = file_reader
        self.chatreplay_adapter = chatreplay_adapter
        self.otlp_adapter = otlp_adapter
        self.copilot_otel_adapter = copilot_otel_adapter or CopilotOTelAdapter()
        self.metrics_calculator = metrics_calculator
        self.cost_calculator = cost_calculator
        self.hotspot_detector = hotspot_detector

    def execute(self, file_path: str) -> ParsedSession:
        """Parse and analyze a session log file."""
        # 1. Read file
        raw_data = self.file_reader.read_file(file_path)

        # 2. Detect format
        format_type = self.file_reader.detect_format(file_path)

        # 3. Adapt format
        context_overhead = None
        if format_type == "chatreplay":
            session, events = self.chatreplay_adapter.adapt(raw_data)
            context_overhead = self.chatreplay_adapter.extract_overhead_data(raw_data)
        elif format_type == "copilot_cli_otel":
            session, events = self.copilot_otel_adapter.adapt(raw_data)
            context_overhead = self.copilot_otel_adapter.extract_overhead_data(raw_data)
        else:  # otlp or default
            session, events = self.otlp_adapter.adapt([raw_data])

        # 4. Calculate metrics
        metrics = self.metrics_calculator.calculate_session_metrics(events, session)

        # 5. Calculate model usage
        model_usage = self.metrics_calculator.calculate_token_usage_by_model(events)
        model_usage = self.cost_calculator.update_model_costs(model_usage)

        # 6. Calculate tool usage
        tool_usage = self.metrics_calculator.calculate_tool_usage(events)

        # 7. Calculate total cost
        total_cost_usd = self.cost_calculator.calculate_session_cost(events)
        total_credits = self.cost_calculator.calculate_credits(total_cost_usd)

        # 8. Detect hotspots
        hotspots = self.hotspot_detector.detect_hotspots(events)

        return ParsedSession(
            session=session,
            events=events,
            metrics=metrics,
            model_usage=model_usage,
            tool_usage=tool_usage,
            hotspots=hotspots,
            total_cost_usd=total_cost_usd,
            total_credits=total_credits,
            context_overhead=context_overhead,
        )
