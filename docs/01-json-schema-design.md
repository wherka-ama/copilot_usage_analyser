# JSON Schema Design for Copilot Debug Logs

## Overview
This document defines the JSON schema for representing GitHub Copilot Agent Debug Log data. The schema is designed to be flexible and accommodate the OpenTelemetry (OTLP) JSON format used by Copilot's debug logs.

## Design Principles
1. **Flexibility**: Accommodate variations in log formats and future changes
2. **Extensibility**: Easy to add new fields without breaking existing parsers
3. **Type Safety**: Clear type definitions for all fields
4. **Traceability**: Maintain relationship between events, sessions, and sub-agents
5. **Analysis-Ready**: Optimized for statistical analysis and reporting

## Core Schema

### Session Level
```json
{
  "session_id": "string (uuid)",
  "title": "string",
  "start_time": "string (ISO 8601)",
  "end_time": "string (ISO 8601)",
  "duration_ms": "number",
  "agent_type": "string (enum: [copilot_cli, claude_cli, vscode, cloud])",
  "model": "string",
  "plan_type": "string (enum: [business, enterprise, individual], default: business)"
}
```

### Metrics Summary
```json
{
  "total_events": "integer",
  "model_turns": "integer",
  "tool_calls": "integer",
  "total_tokens": {
    "input": "integer",
    "output": "integer",
    "cached": "integer"
  },
  "errors": "integer",
  "sub_agents_invoked": "integer"
}
```

### Event Structure
```json
{
  "event_id": "string (uuid)",
  "timestamp": "string (ISO 8601)",
  "event_type": "string (enum: [model_turn, tool_call, discovery, error, sub_agent, custom_agent])",
  "parent_event_id": "string (uuid, optional)",
  "agent_name": "string (optional)",
  "summary": "string",
  "details": {
    "prompt": "string (optional)",
    "response": "string (optional)",
    "tool_name": "string (optional)",
    "tool_input": "object (optional)",
    "tool_output": "object (optional)",
    "error_message": "string (optional)",
    "error_stack": "string (optional)",
    "file_discovered": "string (optional)",
    "customization_loaded": "string (optional)",
    "model": "string (optional)",
    "tokens": {
      "input": "integer (optional)",
      "output": "integer (optional)",
      "cached": "integer (optional)"
    },
    "duration_ms": "number (optional)"
  }
}
```

### Token Usage by Model
```json
{
  "model_name": "string",
  "provider": "string (enum: [openai, anthropic, google, xai, github])",
  "total_input_tokens": "integer",
  "total_output_tokens": "integer",
  "total_cached_tokens": "integer",
  "total_requests": "integer",
  "estimated_cost_usd": "number"
}
```

### Tool Usage Statistics
```json
{
  "tool_name": "string",
  "invocation_count": "integer",
  "success_count": "integer",
  "failure_count": "integer",
  "average_duration_ms": "number",
  "total_tokens_used": "integer"
}
```

### Hotspot Detection
```json
{
  "hotspot_id": "string (uuid)",
  "event_id": "string (uuid)",
  "type": "string (enum: [high_token_usage, long_duration, frequent_failures, excessive_turns])",
  "severity": "string (enum: [low, medium, high])",
  "description": "string",
  "metrics": {
    "token_count": "number (optional)",
    "duration_ms": "number (optional)",
    "failure_count": "number (optional)",
    "turn_count": "number (optional)"
  },
  "context": {
    "task_description": "string",
    "model_used": "string",
    "timestamp": "string (ISO 8601)"
  }
}
```

## Complete Schema Example
```json
{
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Refactor authentication module",
    "start_time": "2026-04-29T10:00:00Z",
    "end_time": "2026-04-29T10:15:30Z",
    "duration_ms": 930000,
    "agent_type": "vscode",
    "model": "gpt-4",
    "plan_type": "business"
  },
  "metrics": {
    "total_events": 45,
    "model_turns": 12,
    "tool_calls": 28,
    "total_tokens": {
      "input": 15000,
      "output": 8000,
      "cached": 2000
    },
    "errors": 2,
    "sub_agents_invoked": 3
  },
  "events": [
    {
      "event_id": "event-001",
      "timestamp": "2026-04-29T10:00:05Z",
      "event_type": "model_turn",
      "summary": "Initial request to refactor authentication",
      "details": {
        "prompt": "Refactor the authentication module...",
        "response": "I'll help you refactor...",
        "model": "gpt-4",
        "tokens": {
          "input": 500,
          "output": 300
        },
        "duration_ms": 2500
      }
    }
  ],
  "token_usage_by_model": [
    {
      "model_name": "gpt-4",
      "provider": "openai",
      "total_input_tokens": 15000,
      "total_output_tokens": 8000,
      "total_cached_tokens": 2000,
      "total_requests": 12,
      "estimated_cost_usd": 0.85
    }
  ],
  "tool_usage": [
    {
      "tool_name": "read_file",
      "invocation_count": 15,
      "success_count": 15,
      "failure_count": 0,
      "average_duration_ms": 50,
      "total_tokens_used": 0
    }
  ],
  "hotspots": [
    {
      "hotspot_id": "hotspot-001",
      "event_id": "event-010",
      "type": "high_token_usage",
      "severity": "high",
      "description": "Code generation task used 3x average tokens",
      "metrics": {
        "token_count": 5000
      },
      "context": {
        "task_description": "Generate unit tests for auth module",
        "model_used": "gpt-4",
        "timestamp": "2026-04-29T10:08:00Z"
      }
    }
  ]
}
```

## Pricing Data (for Cost Calculation)
```json
{
  "pricing": {
    "plan_type": "business",
    "included_credits_per_month": 1900,
    "credit_to_usd_rate": 0.01,
    "model_pricing": {
      "openai": {
        "gpt-4": {
          "input_per_million": 30,
          "output_per_million": 60,
          "cached_read_per_million": 0.1,
          "cached_write_per_million": 30
        }
      },
      "anthropic": {
        "claude-3-5-sonnet": {
          "input_per_million": 3,
          "output_per_million": 15,
          "cache_write_per_million": 3.75
        }
      },
      "google": {
        "gemini-1.5-pro": {
          "input_per_million": 1.25,
          "output_per_million": 5,
          "cached_read_per_million": 0.31
        }
      }
    }
  }
}
```

## Edge Cases and Considerations

### Missing Fields
- Optional fields should be handled gracefully
- Default values for plan_type: "business"
- Null handling for missing token counts

### Multiple Sessions
- Schema supports single session analysis
- Multiple sessions can be processed separately or aggregated

### Model Variations
- Flexible model naming to accommodate future models
- Provider field for categorization

### Time Zones
- All timestamps in ISO 8601 format
- Duration calculations in milliseconds for precision

### Large Files
- JSONL format support for streaming large files
- Event-by-event processing to handle memory constraints
