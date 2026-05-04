"""OTLP adapter for transforming OpenTelemetry format to internal model."""

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from ...domain.entities import AgentType, Event, EventType, PlanType, Session, TokenUsage


class OTLPAdapter:
    """Adapter for transforming OTLP JSON data to internal domain model."""

    def adapt(self, otlp_data: List[Dict]) -> tuple[Session, List[Event]]:
        """Transform OTLP data to internal session and events."""
        if not otlp_data:
            raise ValueError("Empty OTLP data")

        # Extract resource spans
        resource_spans = otlp_data[0].get("resourceSpans", [])
        if not resource_spans:
            raise ValueError("No resourceSpans found in OTLP data")

        resource = resource_spans[0].get("resource", {})
        session = self._extract_session_info(resource)

        # Extract spans as events
        scope_spans = resource_spans[0].get("scopeSpans", [])
        events = []
        for scope_span in scope_spans:
            spans = scope_span.get("spans", [])
            for span in spans:
                event = self._adapt_span(span)
                events.append(event)

        return session, events

    def _extract_session_info(self, resource: Dict) -> Session:
        """Extract session information from resource attributes."""
        attributes = resource.get("attributes", {})
        attrs_dict = {attr["key"]: attr["value"] for attr in attributes}

        session_id = self._parse_uuid(attrs_dict.get("session.id"))
        title = attrs_dict.get("session.title", "Unknown Session")
        start_time = self._parse_timestamp(attrs_dict.get("session.start_time"))
        end_time = self._parse_timestamp(attrs_dict.get("session.end_time"))
        agent_type_str = attrs_dict.get("agent.type", "vscode")
        model = attrs_dict.get("model.name", "gpt-4")
        plan_type_str = attrs_dict.get("plan.type", "business")

        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            agent_type = AgentType.VSCODE

        try:
            plan_type = PlanType(plan_type_str)
        except ValueError:
            plan_type = PlanType.BUSINESS

        return Session(
            session_id=session_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            agent_type=agent_type,
            model=model,
            plan_type=plan_type,
        )

    def _adapt_span(self, span: Dict) -> Event:
        """Transform a span to an event."""
        attributes = span.get("attributes", [])
        attrs_dict = {attr["key"]: attr["value"] for attr in attributes}

        event_id = self._parse_uuid(attrs_dict.get("event.id", str(uuid4())))
        timestamp = self._parse_timestamp(span.get("startTimeUnixNano"))
        event_type_str = attrs_dict.get("event.type", "model_turn")
        summary = attrs_dict.get("summary", "")

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            event_type = EventType.MODEL_TURN

        # Extract token usage
        token_usage = TokenUsage(
            input=attrs_dict.get("token.input", 0),
            output=attrs_dict.get("token.output", 0),
            cached=attrs_dict.get("token.cached", 0),
        )

        duration_ms = self._parse_duration(span.get("startTimeUnixNano"), span.get("endTimeUnixNano"))

        parent_event_id = self._parse_uuid(attrs_dict.get("parent.event.id"))
        agent_name = attrs_dict.get("agent.name")

        # Extract details
        details: Dict[str, Any] = {}
        for key, value in attrs_dict.items():
            if key not in [
                "event.id",
                "event.type",
                "summary",
                "token.input",
                "token.output",
                "token.cached",
                "parent.event.id",
                "agent.name",
            ]:
                details[key] = value

        return Event(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            summary=summary,
            token_usage=token_usage,
            duration_ms=duration_ms,
            parent_event_id=parent_event_id,
            agent_name=agent_name,
            details=details,
        )

    def _parse_uuid(self, value: Any) -> UUID:
        """Parse a UUID from various formats."""
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                return uuid4()
        return uuid4()

    def _parse_timestamp(self, value: Any) -> datetime:
        """Parse a timestamp from various formats."""
        if isinstance(value, datetime):
            # Make naive if it's timezone-aware
            if value.tzinfo is not None:
                return value.replace(tzinfo=None)
            return value
        if isinstance(value, str):
            try:
                # Try Unix nano timestamp
                dt = datetime.fromtimestamp(int(value) / 1e9)
                if dt.tzinfo is not None:
                    return dt.replace(tzinfo=None)
                return dt
            except (ValueError, TypeError):
                pass
            try:
                # Try ISO format
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.tzinfo is not None:
                    return dt.replace(tzinfo=None)
                return dt
            except ValueError:
                pass
        return datetime.utcnow()

    def _parse_duration(self, start: Any, end: Any) -> float:
        """Parse duration from start and end timestamps."""
        start_dt = self._parse_timestamp(start)
        end_dt = self._parse_timestamp(end)
        return (end_dt - start_dt).total_seconds() * 1000
