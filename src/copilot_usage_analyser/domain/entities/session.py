"""Session entity representing a Copilot chat session."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID


class AgentType(Enum):
    """Types of Copilot agents."""

    COPILOT_CLI = "copilot_cli"
    CLAUDE_CLI = "claude_cli"
    VSCODE = "vscode"
    CLOUD = "cloud"


class PlanType(Enum):
    """Copilot plan types for pricing."""

    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    INDIVIDUAL = "individual"


@dataclass(frozen=True)
class Session:
    """Represents a Copilot chat session."""

    session_id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    agent_type: AgentType
    model: str
    plan_type: PlanType = PlanType.BUSINESS

    @property
    def duration(self) -> timedelta:
        """Calculate session duration."""
        return self.end_time - self.start_time

    @property
    def duration_ms(self) -> int:
        """Calculate session duration in milliseconds."""
        return int(self.duration.total_seconds() * 1000)
