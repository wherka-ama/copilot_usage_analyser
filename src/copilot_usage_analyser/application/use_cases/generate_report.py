"""Use case for generating reports."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..domain.entities import Hotspot, HotspotSeverity, ModelTokenUsage, Session, SessionMetrics, ToolUsageStats
from ..infrastructure.charts import ChartGenerator


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    report_type: str = "detailed"
    include_charts: bool = True
    chart_format: str = "png"
    output_format: str = "markdown"


class GenerateReport:
    """Use case for generating reports from analyzed sessions."""

    def __init__(self, chart_generator: ChartGenerator):
        """Initialize with dependencies."""
        self.chart_generator = chart_generator

    def execute(
        self,
        session: Session,
        metrics: SessionMetrics,
        model_usage: List[ModelTokenUsage],
        tool_usage: List[ToolUsageStats],
        hotspots: List[Hotspot],
        total_cost_usd: float,
        total_credits: int,
        config: ReportConfig,
    ) -> str:
        """Generate a markdown report."""
        lines = []

        # Header
        lines.append("# Copilot Usage Analysis Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        lines.append(f"**Session:** {session.title}")
        lines.append(f"**Duration:** {session.duration}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Total Cost:** ${total_cost_usd:.2f} USD ({total_credits} AI credits)")
        lines.append(f"- **Total Events:** {metrics.total_events}")
        lines.append(f"- **Model Turns:** {metrics.model_turns}")
        lines.append(f"- **Tool Calls:** {metrics.tool_calls}")
        lines.append(f"- **Errors:** {metrics.errors}")
        lines.append("")

        # Session Overview
        lines.append("## Session Overview")
        lines.append("")
        lines.append(f"- **Session ID:** {session.session_id}")
        lines.append(f"- **Agent Type:** {session.agent_type.value}")
        lines.append(f"- **Model:** {session.model}")
        lines.append(f"- **Plan Type:** {session.plan_type.value}")
        lines.append(f"- **Start Time:** {session.start_time.isoformat()}")
        lines.append(f"- **End Time:** {session.end_time.isoformat()}")
        lines.append(f"- **Duration:** {session.duration}")
        lines.append("")

        # Usage Statistics
        lines.append("## Usage Statistics")
        lines.append("")
        lines.append(f"- **Total Events:** {metrics.total_events}")
        lines.append(f"- **Model Turns:** {metrics.model_turns}")
        lines.append(f"- **Tool Calls:** {metrics.tool_calls}")
        lines.append(f"- **Sub-agents Invoked:** {metrics.sub_agents_invoked}")
        lines.append(f"- **Errors:** {metrics.errors}")
        lines.append("")

        # Token Analysis
        lines.append("## Token Analysis")
        lines.append("")
        lines.append(f"- **Input Tokens:** {metrics.total_tokens_input:,}")
        lines.append(f"- **Output Tokens:** {metrics.total_tokens_output:,}")
        lines.append(f"- **Cached Tokens:** {metrics.total_tokens_cached:,}")
        lines.append(f"- **Total Tokens:** {metrics.total_tokens_input + metrics.total_tokens_output + metrics.total_tokens_cached:,}")
        lines.append("")

        if config.include_charts and model_usage:
            lines.append("### Token Usage by Model")
            lines.append("")
            model_tokens = {m.model_name: m.total_tokens for m in model_usage}
            chart_path = self.chart_generator.generate_bar_chart(
                model_tokens, "Token Usage by Model", "Model", "Tokens"
            )
            lines.append(f"![Token Usage by Model]({chart_path})")
            lines.append("")

        # Model Performance
        if model_usage:
            lines.append("## Model Performance")
            lines.append("")
            lines.append("| Model | Provider | Input Tokens | Output Tokens | Cached Tokens | Requests | Cost (USD) |")
            lines.append("|-------|----------|--------------|---------------|----------------|----------|------------|")
            for m in model_usage:
                lines.append(
                    f"| {m.model_name} | {m.provider} | {m.total_input_tokens:,} | {m.total_output_tokens:,} | {m.total_cached_tokens:,} | {m.total_requests} | ${m.estimated_cost_usd:.2f} |"
                )
            lines.append("")

        # Tool Usage
        if tool_usage:
            lines.append("## Tool Usage")
            lines.append("")
            lines.append("| Tool | Invocations | Success | Failure | Avg Duration (ms) | Success Rate |")
            lines.append("|------|-------------|---------|---------|-------------------|--------------|")
            for t in tool_usage:
                lines.append(
                    f"| {t.tool_name} | {t.invocation_count} | {t.success_count} | {t.failure_count} | {t.average_duration_ms:.2f} | {t.success_rate:.1%} |"
                )
            lines.append("")

            if config.include_charts:
                tool_counts = {t.tool_name: t.invocation_count for t in tool_usage}
                chart_path = self.chart_generator.generate_bar_chart(
                    tool_counts, "Tool Invocation Counts", "Tool", "Count"
                )
                lines.append(f"![Tool Invocation Counts]({chart_path})")
                lines.append("")

        # Hotspot Analysis
        if hotspots:
            lines.append("## Hotspot Analysis")
            lines.append("")
            lines.append(f"**{len(hotspots)} hotspots detected**")
            lines.append("")
            lines.append("| Severity | Type | Description | Task | Model |")
            lines.append("|----------|------|-------------|------|-------|")
            for h in hotspots:
                lines.append(
                    f"| {h.severity.value} | {h.hotspot_type.value} | {h.description} | {h.task_description or 'N/A'} | {h.model_used or 'N/A'} |"
                )
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        if hotspots:
            lines.append("Based on the analysis, consider the following optimizations:")
            lines.append("")
            for hotspot in hotspots[:5]:
                lines.append(f"- **{hotspot.hotspot_type.value}:** {hotspot.description}")
                if hotspot.severity == HotspotSeverity.HIGH:
                    lines.append("  - Priority: HIGH - Address this issue first")
            lines.append("")
        else:
            lines.append("No significant issues detected. Your usage appears to be efficient.")
            lines.append("")

        return "\n".join(lines)
