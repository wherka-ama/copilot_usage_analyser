"""Metrics entities for session analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID


class HotspotType(Enum):
    """Types of hotspots."""

    HIGH_TOKEN_USAGE = "high_token_usage"
    LONG_DURATION = "long_duration"
    FREQUENT_FAILURES = "frequent_failures"
    EXCESSIVE_TURNS = "excessive_turns"


class HotspotSeverity(Enum):
    """Severity levels for hotspots."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class SessionMetrics:
    """Aggregate metrics for a session."""

    total_events: int
    model_turns: int
    tool_calls: int
    total_tokens_input: int
    total_tokens_output: int
    total_tokens_cached: int
    errors: int
    sub_agents_invoked: int


@dataclass(frozen=True)
class ModelTokenUsage:
    """Token usage grouped by model."""

    model_name: str
    provider: str
    total_input_tokens: int
    total_output_tokens: int
    total_cached_tokens: int
    total_requests: int
    estimated_cost_usd: float

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens."""
        return self.total_input_tokens + self.total_output_tokens + self.total_cached_tokens


@dataclass(frozen=True)
class ToolUsageStats:
    """Statistics for tool usage."""

    tool_name: str
    invocation_count: int
    success_count: int
    failure_count: int
    average_duration_ms: float
    total_tokens_used: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.invocation_count == 0:
            return 0.0
        return self.success_count / self.invocation_count


@dataclass(frozen=True)
class Hotspot:
    """Represents a usage hotspot."""

    hotspot_id: UUID
    event_id: UUID
    hotspot_type: HotspotType
    severity: HotspotSeverity
    description: str
    token_count: Optional[int] = None
    duration_ms: Optional[float] = None
    failure_count: Optional[int] = None
    turn_count: Optional[int] = None
    task_description: Optional[str] = None
    model_used: Optional[str] = None
    timestamp: Optional[str] = None
