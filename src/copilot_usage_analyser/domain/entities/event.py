"""Event entity representing a single event in a session."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class EventType(Enum):
    """Types of events in a Copilot session."""

    MODEL_TURN = "model_turn"
    TOOL_CALL = "tool_call"
    DISCOVERY = "discovery"
    ERROR = "error"
    SUB_AGENT = "sub_agent"
    CUSTOM_AGENT = "custom_agent"


@dataclass(frozen=True)
class TokenUsage:
    """Token usage information."""

    input: int = 0
    output: int = 0
    cached: int = 0

    @property
    def total(self) -> int:
        """Calculate total tokens."""
        return self.input + self.output + self.cached


@dataclass(frozen=True)
class Event:
    """Represents a single event in a Copilot session."""

    event_id: UUID
    timestamp: datetime
    event_type: EventType
    summary: str
    token_usage: TokenUsage
    duration_ms: float
    parent_event_id: Optional[UUID] = None
    agent_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)
