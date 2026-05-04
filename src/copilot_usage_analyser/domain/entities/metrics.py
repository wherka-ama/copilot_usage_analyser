"""Metrics entities for session analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
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


@dataclass(frozen=True)
class ToolRegistrationInfo:
    """Information about a tool registered in the context (available but not necessarily invoked)."""

    name: str
    category: str
    mcp_server: Optional[str]
    definition_tokens_est: int
    invocation_count: int

    @property
    def was_invoked(self) -> bool:
        """Whether this tool was invoked at least once."""
        return self.invocation_count > 0


@dataclass(frozen=True)
class ContextOverheadStats:
    """Statistics about context token overhead per session."""

    total_requests: int
    avg_prompt_tokens: int
    system_prompt_tokens_est: int
    custom_instructions_tokens_est: int
    builtin_tool_tokens_est: int
    mcp_tool_tokens_est: int
    activator_tool_tokens_est: int
    registered_tools: List[ToolRegistrationInfo]

    @property
    def total_tool_tokens_est(self) -> int:
        """Total estimated tokens consumed by all tool definitions."""
        return self.builtin_tool_tokens_est + self.mcp_tool_tokens_est + self.activator_tool_tokens_est

    @property
    def total_overhead_tokens_est(self) -> int:
        """Total estimated overhead tokens (system prompt + tools) per request."""
        return self.system_prompt_tokens_est + self.total_tool_tokens_est

    @property
    def mcp_tools_never_invoked(self) -> List[ToolRegistrationInfo]:
        """MCP tools that were registered but never used."""
        return [t for t in self.registered_tools if t.category == "mcp" and not t.was_invoked]

    @property
    def mcp_never_invoked_tokens_est(self) -> int:
        """Estimated tokens wasted on MCP tools that were never invoked."""
        return sum(t.definition_tokens_est for t in self.mcp_tools_never_invoked)

    @property
    def potential_savings_tokens(self) -> int:
        """Estimated total token savings if all never-invoked MCP tools were removed."""
        return self.mcp_never_invoked_tokens_est * self.total_requests

    @property
    def tools_by_category(self) -> Dict[str, List[ToolRegistrationInfo]]:
        """Group registered tools by category."""
        result: Dict[str, List[ToolRegistrationInfo]] = {}
        for tool in self.registered_tools:
            result.setdefault(tool.category, []).append(tool)
        return result
