"""Metrics calculator service."""

from collections import Counter, defaultdict
from statistics import mean
from typing import List

from ..entities import (
    Event,
    EventType,
    ModelTokenUsage,
    Session,
    SessionMetrics,
    ToolUsageStats,
)


class MetricsCalculator:
    """Service for calculating session metrics."""

    def calculate_session_metrics(
        self, events: List[Event], session: Session
    ) -> SessionMetrics:
        """Calculate aggregate metrics for a session."""
        total_events = len(events)
        model_turns = sum(1 for e in events if e.event_type == EventType.MODEL_TURN)
        tool_calls = sum(1 for e in events if e.event_type == EventType.TOOL_CALL)
        errors = sum(1 for e in events if e.event_type == EventType.ERROR)
        sub_agents = sum(1 for e in events if e.event_type == EventType.SUB_AGENT)

        llm_events = [e for e in events if e.event_type == EventType.MODEL_TURN]
        total_input = sum(e.token_usage.input for e in llm_events)
        total_output = sum(e.token_usage.output for e in llm_events)
        total_cached = sum(e.token_usage.cached for e in llm_events)
        total_reasoning = sum(e.token_usage.reasoning for e in llm_events)

        return SessionMetrics(
            total_events=total_events,
            model_turns=model_turns,
            tool_calls=tool_calls,
            total_tokens_input=total_input,
            total_tokens_output=total_output,
            total_tokens_cached=total_cached,
            errors=errors,
            sub_agents_invoked=sub_agents,
            total_reasoning_tokens=total_reasoning,
        )

    def calculate_token_usage_by_model(
        self, events: List[Event]
    ) -> List[ModelTokenUsage]:
        """Group token usage by model.

        Only MODEL_TURN and SUB_AGENT events carry model/token data. TOOL_CALL
        events have no model and zero tokens, so they are excluded to avoid
        polluting the model table with a spurious 'unknown' row.
        """
        model_data = defaultdict(lambda: {"input": 0, "output": 0, "cached": 0, "reasoning": 0, "requests": 0})

        for event in events:
            if event.event_type == EventType.TOOL_CALL:
                continue
            model = event.details.get("model", "unknown") if event.details else "unknown"
            provider = event.details.get("provider", "unknown") if event.details else "unknown"
            key = (model, provider)

            model_data[key]["input"] += event.token_usage.input
            model_data[key]["output"] += event.token_usage.output
            model_data[key]["cached"] += event.token_usage.cached
            model_data[key]["reasoning"] += event.token_usage.reasoning
            model_data[key]["requests"] += 1

        # Note: Cost calculation will be done by CostCalculator
        return [
            ModelTokenUsage(
                model_name=model,
                provider=provider,
                total_input_tokens=data["input"],
                total_output_tokens=data["output"],
                total_cached_tokens=data["cached"],
                total_requests=data["requests"],
                estimated_cost_usd=0.0,  # Will be calculated by CostCalculator
                total_reasoning_tokens=data["reasoning"],
            )
            for (model, provider), data in model_data.items()
        ]

    def calculate_tool_usage(self, events: List[Event]) -> List[ToolUsageStats]:
        """Calculate tool usage statistics."""
        tool_data = defaultdict(lambda: {"count": 0, "success": 0, "failure": 0, "durations": [], "tokens": 0})

        for event in events:
            if event.event_type == EventType.TOOL_CALL and event.details:
                tool_name = event.details.get("tool_name", "unknown")
                tool_data[tool_name]["count"] += 1
                tool_data[tool_name]["tokens"] += event.token_usage.total

                # Determine success/failure
                if event.event_type == EventType.ERROR:
                    tool_data[tool_name]["failure"] += 1
                else:
                    tool_data[tool_name]["success"] += 1

                if event.duration_ms > 0:
                    tool_data[tool_name]["durations"].append(event.duration_ms)

        return [
            ToolUsageStats(
                tool_name=tool_name,
                invocation_count=data["count"],
                success_count=data["success"],
                failure_count=data["failure"],
                average_duration_ms=mean(data["durations"]) if data["durations"] else 0.0,
                total_tokens_used=data["tokens"],
            )
            for tool_name, data in tool_data.items()
        ]
