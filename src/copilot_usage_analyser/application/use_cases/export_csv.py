"""Use case for exporting token usage data to CSV."""

import csv
from datetime import datetime
from typing import List, Optional

from ...domain.entities import ContextOverheadStats, Hotspot, ModelTokenUsage, Session, SessionMetrics, ToolUsageStats
from ...domain.services import CostCalculator
from ...domain.value_objects import PricingConfig


class ExportCSV:
    """Use case for exporting token usage data to CSV format."""

    def __init__(self, cost_calculator: CostCalculator):
        """Initialize with dependencies."""
        self.cost_calculator = cost_calculator

    def execute(
        self,
        session: Session,
        events: List,
        model_usage: List[ModelTokenUsage],
        tool_usage: List[ToolUsageStats],
        hotspots: List[Hotspot],
        total_cost_usd: float,
        pricing_config: Optional[PricingConfig] = None,
        context_overhead: Optional[ContextOverheadStats] = None,
    ) -> str:
        """Generate CSV content with detailed token usage breakdown."""
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "timestamp",
            "event_type",
            "event_id",
            "model",
            "provider",
            "input_tokens",
            "output_tokens",
            "cached_tokens",
            "total_tokens",
            "cost_usd",
            "tool_name",
            "tool_success",
            "duration_ms",
            "summary",
        ])

        # Write event rows
        for event in events:
            timestamp = event.timestamp.isoformat() if event.timestamp else ""
            event_type = event.event_type
            event_id = event.event_id
            model = event.details.get("model", "") if event.details else ""
            provider = event.details.get("provider", "") if event.details else ""
            
            input_tokens = event.token_usage.input if event.token_usage else 0
            output_tokens = event.token_usage.output if event.token_usage else 0
            cached_tokens = event.token_usage.cached if event.token_usage else 0
            total_tokens = input_tokens + output_tokens + cached_tokens
            
            cost_usd = 0.0
            if pricing_config and event.token_usage:
                cost_usd = self.cost_calculator.calculate_event_cost(event)
            
            tool_name = event.details.get("tool_name", "") if event.details else ""
            tool_success = event.details.get("success", "") if event.details else ""
            duration_ms = event.details.get("duration_ms", "") if event.details else ""
            summary = event.summary if event.summary else ""

            writer.writerow([
                timestamp,
                event_type,
                event_id,
                model,
                provider,
                input_tokens,
                output_tokens,
                cached_tokens,
                total_tokens,
                f"{cost_usd:.6f}" if cost_usd else "",
                tool_name,
                tool_success,
                duration_ms,
                summary,
            ])

        # Write summary section
        writer.writerow([])
        writer.writerow(["# SUMMARY"])
        writer.writerow(["session_id", session.session_id])
        writer.writerow(["session_title", session.title])
        writer.writerow(["start_time", session.start_time.isoformat() if session.start_time else ""])
        writer.writerow(["end_time", session.end_time.isoformat() if session.end_time else ""])
        writer.writerow(["duration", str(session.duration)])
        writer.writerow(["agent_type", session.agent_type.value if session.agent_type else ""])
        writer.writerow(["model", session.model])
        writer.writerow(["total_events", str(len(events))])
        writer.writerow(["total_cost_usd", f"{total_cost_usd:.6f}"])

        # Write model usage summary
        writer.writerow([])
        writer.writerow(["# MODEL USAGE"])
        writer.writerow(["model", "provider", "input_tokens", "output_tokens", "cached_tokens", "total_tokens", "requests", "cost_usd"])
        for mu in model_usage:
            writer.writerow([
                mu.model_name,
                mu.provider,
                mu.total_input_tokens,
                mu.total_output_tokens,
                mu.total_cached_tokens,
                mu.total_tokens,
                mu.total_requests,
                f"{mu.estimated_cost_usd:.6f}",
            ])

        # Write tool usage summary
        writer.writerow([])
        writer.writerow(["# TOOL USAGE"])
        writer.writerow(["tool_name", "invocations", "success_count", "failure_count", "avg_duration_ms", "success_rate"])
        for tu in tool_usage:
            success_rate = f"{tu.success_rate:.1%}" if tu.invocation_count > 0 else "0%"
            writer.writerow([
                tu.tool_name,
                tu.invocation_count,
                tu.success_count,
                tu.failure_count,
                f"{tu.average_duration_ms:.2f}" if tu.average_duration_ms else "",
                success_rate,
            ])

        # Write context overhead summary if available
        if context_overhead:
            writer.writerow([])
            writer.writerow(["# CONTEXT OVERHEAD"])
            writer.writerow(["total_requests", context_overhead.total_requests])
            writer.writerow(["avg_prompt_tokens", context_overhead.avg_prompt_tokens])
            writer.writerow(["system_prompt_tokens_est", context_overhead.system_prompt_tokens_est])
            writer.writerow(["custom_instructions_tokens_est", context_overhead.custom_instructions_tokens_est])
            writer.writerow(["builtin_tool_tokens_est", context_overhead.builtin_tool_tokens_est])
            writer.writerow(["mcp_tool_tokens_est", context_overhead.mcp_tool_tokens_est])
            writer.writerow(["activator_tool_tokens_est", context_overhead.activator_tool_tokens_est])
            writer.writerow(["total_overhead_tokens_est", context_overhead.total_overhead_tokens_est])

            writer.writerow([])
            writer.writerow(["# TOOL REGISTRATION"])
            writer.writerow(["tool_name", "category", "mcp_server", "definition_tokens_est", "invocation_count", "was_invoked"])
            for tool in context_overhead.registered_tools:
                writer.writerow([
                    tool.name,
                    tool.category,
                    tool.mcp_server,
                    tool.definition_tokens_est,
                    tool.invocation_count,
                    "true" if tool.was_invoked else "false",
                ])

        # Write hotspots summary
        if hotspots:
            writer.writerow([])
            writer.writerow(["# HOTSPOTS"])
            writer.writerow(["hotspot_id", "type", "severity", "description", "token_count", "duration_ms"])
            for hs in hotspots:
                writer.writerow([
                    hs.hotspot_id,
                    hs.hotspot_type.value,
                    hs.severity.value,
                    hs.description,
                    hs.token_count if hs.token_count else "",
                    hs.duration_ms if hs.duration_ms else "",
                ])

        return output.getvalue()
