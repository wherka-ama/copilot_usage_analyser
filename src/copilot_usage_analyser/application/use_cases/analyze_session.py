"""Use case for analyzing a Copilot session."""

from dataclasses import dataclass
from typing import List

from ..domain.entities import Hotspot, ModelTokenUsage, Session, SessionMetrics, ToolUsageStats
from ..domain.services import CostCalculator, HotspotDetector, MetricsCalculator
from ..infrastructure.adapters import OTLPAdapter
from ..infrastructure.readers import LogFileReader


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


class AnalyzeSession:
    """Use case for analyzing a Copilot session log file."""

    def __init__(
        self,
        file_reader: LogFileReader,
        otlp_adapter: OTLPAdapter,
        metrics_calculator: MetricsCalculator,
        cost_calculator: CostCalculator,
        hotspot_detector: HotspotDetector,
    ):
        """Initialize with dependencies."""
        self.file_reader = file_reader
        self.adapter = otlp_adapter
        self.metrics_calculator = metrics_calculator
        self.cost_calculator = cost_calculator
        self.hotspot_detector = hotspot_detector

    def execute(self, file_path: str) -> ParsedSession:
        """Parse and analyze a session log file."""
        # 1. Read file
        raw_data = list(self.file_reader.read_file(file_path))

        # 2. Adapt format
        session, events = self.adapter.adapt(raw_data)

        # 3. Calculate metrics
        metrics = self.metrics_calculator.calculate_session_metrics(events, session)

        # 4. Calculate model usage
        model_usage = self.metrics_calculator.calculate_token_usage_by_model(events)
        model_usage = self.cost_calculator.update_model_costs(model_usage)

        # 5. Calculate tool usage
        tool_usage = self.metrics_calculator.calculate_tool_usage(events)

        # 6. Calculate total cost
        total_cost_usd = self.cost_calculator.calculate_session_cost(events)
        total_credits = self.cost_calculator.calculate_credits(total_cost_usd)

        # 7. Detect hotspots
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
        )
