"""Copilot CLI OTel adapter for transforming JSONL span/metric format to internal model."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ...domain.entities import (
    AgentType,
    ContextOverheadStats,
    Event,
    EventType,
    PlanType,
    Session,
    TokenUsage,
    ToolRegistrationInfo,
)


class CopilotOTelAdapter:
    """Adapter for Copilot CLI OTel JSONL export format.

    Each line is a JSON object with type 'span' or 'metric'.
    Span names map to:
      - 'invoke_agent' → SUB_AGENT / CUSTOM_AGENT event (top-level orchestration)
      - 'chat <model>'  → MODEL_TURN event (individual LLM call)
      - 'execute_tool <tool>' → TOOL_CALL event
    """

    def adapt(self, records: List[Dict]) -> Tuple[Session, List[Event]]:
        """Transform flat OTel records list to internal session and events."""
        if not records:
            raise ValueError("Empty OTel data")

        spans = [r for r in records if r.get("type") == "span"]
        if not spans:
            raise ValueError("No span records found in OTel data")

        session = self._extract_session(spans)
        events = []
        for span in spans:
            event = self._adapt_span(span)
            if event is not None:
                events.append(event)

        events.sort(key=lambda e: e.timestamp)
        return session, events

    def extract_overhead_data(self, records: List[Dict]) -> Optional[ContextOverheadStats]:
        """Extract context overhead stats from OTel records.

        Tool definitions are embedded as JSON strings in invoke_agent / chat spans.
        """
        spans = [r for r in records if r.get("type") == "span"]

        registered_tools_raw: List[Dict] = []
        invoked_tool_names: Dict[str, int] = {}
        prompt_token_counts: List[int] = []

        for span in spans:
            attrs = span.get("attributes", {})
            op = attrs.get("gen_ai.operation.name", "")

            # Collect registered tools from the first span that has them
            if op in ("chat", "invoke_agent") and not registered_tools_raw:
                raw_defs = attrs.get("gen_ai.tool.definitions", "")
                if raw_defs:
                    try:
                        defs = json.loads(raw_defs)
                        if isinstance(defs, list):
                            registered_tools_raw = defs
                    except (json.JSONDecodeError, TypeError):
                        pass

            # Collect token counts from chat spans (total = input + cache_read + cache_creation)
            if op == "chat":
                inp = int(attrs.get("gen_ai.usage.input_tokens", 0))
                if inp:
                    prompt_token_counts.append(inp)

            # Collect invoked tools
            if op == "execute_tool":
                tool_name = attrs.get("gen_ai.tool.name", "")
                if tool_name:
                    invoked_tool_names[tool_name] = invoked_tool_names.get(tool_name, 0) + 1

        if not prompt_token_counts and not registered_tools_raw:
            return None

        # Build ToolRegistrationInfo list (OTel tool defs are minimal: {type, name})
        tool_infos: List[ToolRegistrationInfo] = []
        for tool_def in registered_tools_raw:
            name = tool_def.get("name", "")
            if not name:
                continue
            tokens_est = max(len(json.dumps(tool_def)) // 4, 5)

            if "-" in name:
                # OTel uses dash-separated prefix for MCP (e.g. github-mcp-server-get_commit)
                parts = name.split("-", 3)
                if len(parts) >= 3 and parts[1] == "mcp":
                    category = "mcp"
                    mcp_server = "-".join(parts[:3])
                else:
                    # Heuristic: if it looks like "servername-toolname" (external)
                    category = "mcp"
                    mcp_server = parts[0]
            elif name.startswith("activate_"):
                category = "activator"
                mcp_server = None
            else:
                category = "builtin"
                mcp_server = None

            tool_infos.append(ToolRegistrationInfo(
                name=name,
                category=category,
                mcp_server=mcp_server,
                definition_tokens_est=tokens_est,
                invocation_count=invoked_tool_names.get(name, 0),
            ))

        builtin_tokens = sum(t.definition_tokens_est for t in tool_infos if t.category == "builtin")
        mcp_tokens = sum(t.definition_tokens_est for t in tool_infos if t.category == "mcp")
        activator_tokens = sum(t.definition_tokens_est for t in tool_infos if t.category == "activator")

        avg_prompt = (
            sum(prompt_token_counts) // len(prompt_token_counts)
            if prompt_token_counts else 0
        )

        return ContextOverheadStats(
            total_requests=len(prompt_token_counts),
            avg_prompt_tokens=avg_prompt,
            system_prompt_tokens_est=0,
            custom_instructions_tokens_est=0,
            builtin_tool_tokens_est=builtin_tokens,
            mcp_tool_tokens_est=mcp_tokens,
            activator_tool_tokens_est=activator_tokens,
            registered_tools=tool_infos,
        )

    def _extract_session(self, spans: List[Dict]) -> Session:
        """Build a Session from span metadata."""
        service_name = "github-copilot"
        service_version = ""
        model = "unknown"
        conversation_id = None

        timestamps = []
        for span in spans:
            resource = span.get("resource", {})
            res_attrs = resource.get("attributes", {})
            service_name = res_attrs.get("service.name", service_name)
            service_version = res_attrs.get("service.version", service_version)

            attrs = span.get("attributes", {})
            op = attrs.get("gen_ai.operation.name", "")
            if op in ("chat", "invoke_agent"):
                m = attrs.get("gen_ai.request.model") or attrs.get("gen_ai.response.model")
                if m:
                    model = m
                if not conversation_id:
                    conversation_id = attrs.get("gen_ai.conversation.id")

            start = self._parse_otel_time(span.get("startTime"))
            end = self._parse_otel_time(span.get("endTime"))
            if start:
                timestamps.append(start)
            if end:
                timestamps.append(end)

        if timestamps:
            start_time = min(timestamps)
            end_time = max(timestamps)
        else:
            start_time = datetime.utcnow()
            end_time = datetime.utcnow()

        title = f"Copilot CLI OTel Session"
        if conversation_id:
            title = f"Copilot CLI Session ({conversation_id[:8]}…)"

        return Session(
            session_id=uuid4(),
            title=title,
            start_time=start_time,
            end_time=end_time,
            agent_type=AgentType.COPILOT_CLI,
            model=model,
            plan_type=PlanType.BUSINESS,
        )

    def _adapt_span(self, span: Dict) -> Optional[Event]:
        """Convert a single span record to an Event (or None for non-events)."""
        attrs = span.get("attributes", {})
        op = attrs.get("gen_ai.operation.name", "")

        if op == "chat":
            return self._adapt_chat_span(span, attrs)
        elif op == "execute_tool":
            return self._adapt_tool_span(span, attrs)
        elif op == "invoke_agent":
            return self._adapt_agent_span(span, attrs)
        return None

    def _adapt_chat_span(self, span: Dict, attrs: Dict) -> Event:
        """Map a 'chat' span to a MODEL_TURN event.

        OTel distinguishes two cache token types:
          - cache_read.input_tokens:    tokens served from cache (cheap/free reads)
          - cache_creation.input_tokens: tokens written to cache (full-price writes)
        TokenUsage.cached holds cache_read only (matches Copilot CLI "cached" display).
        cache_creation is stored in details for accurate cost calculation.
        """
        model = attrs.get("gen_ai.response.model") or attrs.get("gen_ai.request.model", "unknown")
        provider = self._infer_provider(model)
        inp = int(attrs.get("gen_ai.usage.input_tokens", 0))
        out = int(attrs.get("gen_ai.usage.output_tokens", 0))
        cache_read = int(attrs.get("gen_ai.usage.cache_read.input_tokens", 0))
        cache_creation = int(attrs.get("gen_ai.usage.cache_creation.input_tokens", 0))
        reasoning = int(attrs.get("gen_ai.usage.reasoning.output_tokens", 0))
        cost_credits = attrs.get("github.copilot.cost", 0)
        conv_id = attrs.get("gen_ai.conversation.id", "")
        turn_id = attrs.get("github.copilot.turn_id", "")

        start = self._parse_otel_time(span.get("startTime")) or datetime.utcnow()
        end = self._parse_otel_time(span.get("endTime")) or start
        duration_ms = (end - start).total_seconds() * 1000

        trace_id = span.get("traceId", "")
        span_id = span.get("spanId", "")
        parent_span_id = span.get("parentSpanId", "")

        return Event(
            event_id=self._span_to_uuid(span_id or str(uuid4())),
            timestamp=start,
            event_type=EventType.MODEL_TURN,
            summary=f"chat {model} turn={turn_id}",
            token_usage=TokenUsage(input=inp, output=out, cached=cache_read, reasoning=reasoning),
            duration_ms=duration_ms,
            parent_event_id=self._span_to_uuid(parent_span_id) if parent_span_id else None,
            agent_name=attrs.get("gen_ai.agent.id"),
            details={
                "model": model,
                "provider": provider,
                "conversation_id": conv_id,
                "turn_id": turn_id,
                "cost_credits": cost_credits,
                "trace_id": trace_id,
                "finish_reasons": attrs.get("gen_ai.response.finish_reasons", []),
                "cache_creation_tokens": cache_creation,
            },
        )

    def _adapt_tool_span(self, span: Dict, attrs: Dict) -> Event:
        """Map an 'execute_tool' span to a TOOL_CALL event."""
        tool_name = attrs.get("gen_ai.tool.name", span.get("name", "unknown"))
        call_id = attrs.get("gen_ai.tool.call.id", "")

        start = self._parse_otel_time(span.get("startTime")) or datetime.utcnow()
        end = self._parse_otel_time(span.get("endTime")) or start
        duration_ms = (end - start).total_seconds() * 1000

        status_code = span.get("status", {}).get("code", 0)
        success = status_code == 0

        span_id = span.get("spanId", "")
        parent_span_id = span.get("parentSpanId", "")

        return Event(
            event_id=self._span_to_uuid(span_id or str(uuid4())),
            timestamp=start,
            event_type=EventType.TOOL_CALL,
            summary=f"execute_tool {tool_name}",
            token_usage=TokenUsage(),
            duration_ms=duration_ms,
            parent_event_id=self._span_to_uuid(parent_span_id) if parent_span_id else None,
            agent_name=None,
            details={
                "tool_name": tool_name,
                "call_id": call_id,
                "success": success,
                "duration_ms": duration_ms,
            },
        )

    def _adapt_agent_span(self, span: Dict, attrs: Dict) -> Event:
        """Map an 'invoke_agent' span to a SUB_AGENT event.

        Token counts are intentionally zeroed here. The invoke_agent span
        aggregates the totals from its child 'chat' spans, which are already
        captured as individual MODEL_TURN events. Counting both would double
        every token.
        """
        agent_id = attrs.get("gen_ai.agent.id", "unknown")
        model = attrs.get("gen_ai.request.model", "unknown")
        turn_count = attrs.get("github.copilot.turn_count", 1)
        cost_credits = attrs.get("github.copilot.cost", 0)

        start = self._parse_otel_time(span.get("startTime")) or datetime.utcnow()
        end = self._parse_otel_time(span.get("endTime")) or start
        duration_ms = (end - start).total_seconds() * 1000

        span_id = span.get("spanId", "")

        return Event(
            event_id=self._span_to_uuid(span_id or str(uuid4())),
            timestamp=start,
            event_type=EventType.SUB_AGENT,
            summary=f"invoke_agent {agent_id} ({turn_count} turns)",
            token_usage=TokenUsage(),
            duration_ms=duration_ms,
            parent_event_id=None,
            agent_name=agent_id,
            details={
                "model": model,
                "provider": self._infer_provider(model),
                "agent_id": agent_id,
                "turn_count": turn_count,
                "cost_credits": cost_credits,
            },
        )

    def _parse_otel_time(self, value: Any) -> Optional[datetime]:
        """Parse OTel [seconds, nanoseconds] timestamp tuple."""
        if isinstance(value, (list, tuple)) and len(value) == 2:
            try:
                seconds = int(value[0]) + int(value[1]) / 1e9
                return datetime.utcfromtimestamp(seconds)
            except (TypeError, ValueError):
                return None
        if isinstance(value, (int, float)):
            try:
                return datetime.utcfromtimestamp(value)
            except (TypeError, ValueError, OSError):
                return None
        return None

    def _span_to_uuid(self, span_id: str) -> UUID:
        """Convert a hex span ID to a UUID (padding to 32 hex chars)."""
        if not span_id:
            return uuid4()
        try:
            padded = span_id.zfill(32)[:32]
            return UUID(padded)
        except ValueError:
            return uuid4()

    def _infer_provider(self, model: str) -> str:
        """Infer provider from model name."""
        m = model.lower()
        if "gpt" in m or "openai" in m or "o1" in m or "o3" in m:
            return "openai"
        if "claude" in m or "anthropic" in m:
            return "anthropic"
        if "gemini" in m or "google" in m:
            return "google"
        if "grok" in m or "xai" in m:
            return "xai"
        return "github"
