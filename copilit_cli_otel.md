$ copilot help monitoring
Monitoring with OpenTelemetry:

  The CLI can export traces and metrics via OpenTelemetry (OTel), giving you visibility into
  agent interactions, LLM calls, tool executions, and token usage. All signal names and
  attributes follow the OTel GenAI Semantic Conventions, so the data works with any
  OTel-compatible backend (Jaeger, Grafana, Azure Monitor, Datadog, Honeycomb, Langfuse, etc.).

  OTel is off by default. When disabled, no instrumentation or exporters are initialized.

Activation:

  OTel activates when any of these conditions are met:

  - COPILOT_OTEL_ENABLED=true
  - OTEL_EXPORTER_OTLP_ENDPOINT is set
  - COPILOT_OTEL_FILE_EXPORTER_PATH is set

Environment Variables:

  COPILOT_OTEL_ENABLED                                 Explicitly enable OTel; defaults to "false".

  OTEL_EXPORTER_OTLP_ENDPOINT                          OTLP endpoint URL. Setting this auto-enables OTel.

  COPILOT_OTEL_EXPORTER_TYPE                           Exporter type: "otlp-http" (default) or "file".
                                                       Auto-selects "file" when COPILOT_OTEL_FILE_EXPORTER_PATH is set.

  COPILOT_OTEL_FILE_EXPORTER_PATH                      Write all signals to this file as JSON-lines.
                                                       Setting this auto-enables OTel.

  COPILOT_OTEL_SOURCE_NAME                             Instrumentation scope name; defaults to "github.copilot".

  OTEL_SERVICE_NAME                                    Service name in resource attributes; defaults to "github-copilot".

  OTEL_RESOURCE_ATTRIBUTES                             Extra resource attributes (comma-separated key=value pairs;
                                                       use percent-encoding for special characters).

  OTEL_EXPORTER_OTLP_HEADERS                           Auth headers for the OTLP exporter
                                                       (e.g., "Authorization=Bearer token").
                                                       Prefer env files or a secret manager over inline tokens.

  OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT   Capture full prompt/response content; defaults to "false".
                                                       See "Content Capture" below.

  OTEL_LOG_LEVEL                                       OTel diagnostic log level (not the CLI --log-level).
                                                       One of: NONE, ERROR, WARN, INFO, DEBUG, VERBOSE, ALL.

What Gets Exported:

  Traces — a hierarchical span tree for each agent interaction:

    invoke_agent                               Agent orchestration (all LLM calls + tool executions)
      chat <model>                             Individual LLM API call
      execute_tool <tool>                      Individual tool invocation

  Spans carry attributes such as model name, token counts, durations, costs, and error info.
  Subagent invocations are automatically linked into the same trace via context propagation.

  Metrics:

    gen_ai.client.operation.duration           LLM/agent call duration (histogram, seconds)
    gen_ai.client.token.usage                  Token counts by type (histogram, tokens)
    github.copilot.tool.call.count             Tool invocations (counter)
    github.copilot.tool.call.duration          Tool execution latency (histogram, seconds)
    github.copilot.agent.turn.count            LLM round-trips per invocation (histogram)

Content Capture:

  By default, no prompt content, responses, or tool arguments are captured — only metadata.
  Set OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true to also capture:

  - Full prompt and response messages
  - System instructions and tool definitions
  - Tool call arguments and results

  Warning: content capture may include sensitive information such as code, file contents,
  and user prompts. Only enable in trusted environments.

Examples:

  # OTLP/HTTP to a local collector (e.g., Jaeger)
  $ OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 copilot

  # File-based output (offline / CI)
  $ COPILOT_OTEL_FILE_EXPORTER_PATH=/tmp/copilot-otel.jsonl copilot

  # Remote collector with authentication and content capture
  $ OTEL_EXPORTER_OTLP_ENDPOINT=https://collector.example.com:4318 \
    OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer your-token" \
    OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true \
    copilot

For full details on span attributes, metric definitions, span events, and advanced
configuration, see the monitoring guide at docs/cli/reference/monitoring.md.
