"""ChatReplay adapter for transforming VS Code chat replay format to internal model."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from ...domain.entities import AgentType, ContextOverheadStats, Event, EventType, PlanType, Session, TokenUsage, ToolRegistrationInfo


class ChatReplayAdapter:
    """Adapter for transforming VS Code Chat Replay JSON data to internal domain model."""

    def adapt(self, chatreplay_data: Dict) -> Tuple[Session, List[Event]]:
        """Transform ChatReplay data to internal session and events."""
        if not chatreplay_data:
            raise ValueError("Empty ChatReplay data")

        # Extract session info
        session = self._extract_session_info(chatreplay_data)

        # Extract events from prompts
        events = []
        prompts = chatreplay_data.get("prompts", [])

        for prompt_data in prompts:
            prompt_events = self._extract_events_from_prompt(prompt_data)
            events.extend(prompt_events)

        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)

        return session, events

    def _extract_session_info(self, data: Dict) -> Session:
        """Extract session information from ChatReplay root."""
        exported_at = data.get("exportedAt")
        total_prompts = data.get("totalPrompts", 0)
        total_log_entries = data.get("totalLogEntries", 0)

        # Extract timestamps from events to determine session bounds
        prompts = data.get("prompts", [])
        timestamps = []

        for prompt in prompts:
            logs = prompt.get("logs", [])
            for log in logs:
                metadata = log.get("metadata", {})
                if metadata.get("startTime"):
                    timestamps.append(self._parse_timestamp(metadata["startTime"]))
                if metadata.get("endTime"):
                    timestamps.append(self._parse_timestamp(metadata["endTime"]))
                if log.get("time"):
                    timestamps.append(self._parse_timestamp(log["time"]))

        if timestamps:
            start_time = min(timestamps)
            end_time = max(timestamps)
        else:
            start_time = datetime.utcnow()
            end_time = datetime.utcnow()

        # Infer model from first request event
        model = "gpt-4"
        for prompt in prompts:
            logs = prompt.get("logs", [])
            for log in logs:
                metadata = log.get("metadata", {})
                if metadata.get("model"):
                    model = metadata["model"]
                    break
            if model != "gpt-4":
                break

        return Session(
            session_id=uuid4(),
            title=f"Chat Session ({total_prompts} prompts)",
            start_time=self._parse_timestamp(start_time),
            end_time=self._parse_timestamp(end_time),
            agent_type=AgentType.VSCODE,
            model=model,
            plan_type=PlanType.BUSINESS,
        )

    def _extract_events_from_prompt(self, prompt_data: Dict) -> List[Event]:
        """Extract events from a single prompt."""
        events = []
        logs = prompt_data.get("logs", [])
        prompt_text = prompt_data.get("prompt", "")

        for log in logs:
            event = self._adapt_log(log, prompt_text)
            if event:
                events.append(event)

        return events

    def _adapt_log(self, log: Dict, prompt_text: str) -> Event:
        """Transform a single log entry to an event."""
        kind = log.get("kind")

        if kind == "toolCall":
            return self._adapt_tool_call(log, prompt_text)
        elif kind == "request":
            return self._adapt_request(log, prompt_text)
        else:
            return None

    def _adapt_tool_call(self, log: Dict, prompt_text: str) -> Event:
        """Transform a tool call log to an event."""
        tool_name = log.get("tool", "unknown")
        args = log.get("args", "")
        time_str = log.get("time")
        response = log.get("response", [])
        thinking = log.get("thinking", {}).get("text", "")

        # Parse tool args to extract context
        try:
            import json
            args_dict = json.loads(args) if args else {}
        except:
            args_dict = {}

        event_id = self._parse_uuid(log.get("id"))
        timestamp = self._parse_timestamp(time_str)

        summary = f"Tool call: {tool_name}"
        if thinking:
            summary = thinking[:100] if len(thinking) > 100 else thinking

        details = {
            "tool_name": tool_name,
            "tool_args": args_dict,
            "request_type": "tool_call",
        }

        if thinking:
            details["thinking"] = thinking

        return Event(
            event_id=event_id,
            timestamp=timestamp,
            event_type=EventType.TOOL_CALL,
            summary=summary,
            token_usage=TokenUsage(input=0, output=0, cached=0),
            duration_ms=0,
            details=details,
        )

    def _adapt_request(self, log: Dict, prompt_text: str) -> Event:
        """Transform a request log to an event."""
        metadata = log.get("metadata", {})
        usage = metadata.get("usage", {})

        event_id = self._parse_uuid(log.get("id"))
        timestamp = self._parse_timestamp(metadata.get("startTime"))
        duration_ms = metadata.get("duration", 0)

        # Extract token usage
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cached_tokens = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        token_usage = TokenUsage(
            input=prompt_tokens,
            output=completion_tokens,
            cached=cached_tokens,
        )

        # Determine event type
        request_type = metadata.get("requestType", "")
        event_type = EventType.MODEL_TURN

        summary = f"Request: {request_type}"
        if prompt_text:
            summary = prompt_text[:100] if len(prompt_text) > 100 else prompt_text

        # Extract model and provider
        model = metadata.get("model", "gpt-4")
        provider = self._infer_provider(model)

        details = {
            "model": model,
            "provider": provider,
            "request_type": request_type,
            "request_id": metadata.get("requestId"),
            "time_to_first_token": metadata.get("timeToFirstToken"),
            "max_prompt_tokens": metadata.get("maxPromptTokens"),
            "max_response_tokens": metadata.get("maxResponseTokens"),
        }

        # Add response if available
        response = log.get("response", {})
        if response.get("message"):
            details["response"] = response["message"]

        return Event(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            summary=summary,
            token_usage=token_usage,
            duration_ms=duration_ms,
            details=details,
        )

    def extract_overhead_data(self, chatreplay_data: Dict) -> Optional[ContextOverheadStats]:
        """Extract context overhead statistics from ChatReplay data."""
        if not chatreplay_data:
            return None

        prompts = chatreplay_data.get("prompts", [])

        # Collect tool registrations (from the first request with tools, they're stable per session)
        registered_tools_raw: List[Dict] = []
        system_prompt_chars = 0
        custom_instructions_chars = 0
        invoked_tool_names: Dict[str, int] = {}
        prompt_token_counts: List[int] = []

        for prompt in prompts:
            logs = prompt.get("logs", [])
            for log in logs:
                kind = log.get("kind")
                if kind == "toolCall":
                    tool_name = log.get("tool", "")
                    if tool_name:
                        invoked_tool_names[tool_name] = invoked_tool_names.get(tool_name, 0) + 1
                elif kind == "request":
                    meta = log.get("metadata", {})
                    usage = meta.get("usage", {})
                    pt = usage.get("prompt_tokens", 0)
                    if pt > 0:
                        prompt_token_counts.append(pt)

                    tools = meta.get("tools", [])
                    if tools and not registered_tools_raw:
                        registered_tools_raw = tools

                    if not system_prompt_chars:
                        messages = log.get("requestMessages", {}).get("messages", [])
                        for msg in messages:
                            if msg.get("role") == 0:
                                for part in (msg.get("content") or []):
                                    if isinstance(part, dict) and part.get("type") == 1:
                                        text = part.get("text", "")
                                        total_chars = len(text)
                                        instr_start = text.find("<instructions>")
                                        instr_end = text.find("</instructions>")
                                        if instr_start >= 0 and instr_end >= 0:
                                            custom_instructions_chars = instr_end + len("</instructions>") - instr_start
                                            system_prompt_chars = total_chars - custom_instructions_chars
                                        else:
                                            system_prompt_chars = total_chars

        if not prompt_token_counts:
            return None

        # Build ToolRegistrationInfo list
        tool_infos: List[ToolRegistrationInfo] = []
        for tool_def in registered_tools_raw:
            name = tool_def.get("name", "")
            tokens_est = len(json.dumps(tool_def)) // 4

            if name.startswith("mcp_"):
                category = "mcp"
                parts = name.split("_", 2)
                mcp_server = parts[1] if len(parts) > 1 else None
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

        return ContextOverheadStats(
            total_requests=len(prompt_token_counts),
            avg_prompt_tokens=sum(prompt_token_counts) // len(prompt_token_counts),
            system_prompt_tokens_est=system_prompt_chars // 4,
            custom_instructions_tokens_est=custom_instructions_chars // 4,
            builtin_tool_tokens_est=builtin_tokens,
            mcp_tool_tokens_est=mcp_tokens,
            activator_tool_tokens_est=activator_tokens,
            registered_tools=tool_infos,
        )

    def _infer_provider(self, model: str) -> str:
        """Infer provider from model name."""
        model_lower = model.lower()
        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower or "google" in model_lower:
            return "google"
        elif "grok" in model_lower or "xai" in model_lower:
            return "xai"
        else:
            return "unknown"

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
                # Try ISO format and make it naive
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.tzinfo is not None:
                    return dt.replace(tzinfo=None)
                return dt
            except ValueError:
                pass
        return datetime.utcnow()
