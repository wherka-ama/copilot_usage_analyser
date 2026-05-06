"""Use case for generating reports."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ...domain.entities import ContextOverheadStats, Hotspot, HotspotSeverity, ModelTokenUsage, Session, SessionMetrics, ToolUsageStats
from ...domain.value_objects import PricingConfig
from ...infrastructure.charts import ChartGenerator


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    report_type: str = "detailed"
    include_charts: bool = True
    chart_format: str = "png"
    output_format: str = "markdown"


class GenerateReport:
    """Use case for generating reports from analyzed sessions."""

    def __init__(self, chart_generator: ChartGenerator):
        """Initialize with dependencies."""
        self.chart_generator = chart_generator

    def execute(
        self,
        session: Session,
        metrics: SessionMetrics,
        model_usage: List[ModelTokenUsage],
        tool_usage: List[ToolUsageStats],
        hotspots: List[Hotspot],
        total_cost_usd: float,
        total_credits: int,
        config: ReportConfig,
        pricing_config: Optional[PricingConfig] = None,
        context_overhead: Optional[ContextOverheadStats] = None,
    ) -> str:
        """Generate a markdown report."""
        lines = []

        # Header
        lines.append("# Copilot Usage Analysis Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        lines.append(f"**Session:** {session.title}")
        lines.append(f"**Duration:** {session.duration}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Total Cost:** ${total_cost_usd:.4f} USD ({total_credits} AI credits)")
        lines.append(f"- **Total Events:** {metrics.total_events}")
        lines.append(f"- **Model Turns:** {metrics.model_turns}")
        lines.append(f"- **Tool Calls:** {metrics.tool_calls}")
        lines.append(f"- **Errors:** {metrics.errors}")
        lines.append("")

        # Session Overview
        lines.append("## Session Overview")
        lines.append("")
        lines.append(f"- **Session ID:** {session.session_id}")
        lines.append(f"- **Agent Type:** {session.agent_type.value}")
        lines.append(f"- **Model:** {session.model}")
        lines.append(f"- **Plan Type:** {session.plan_type.value}")
        lines.append(f"- **Start Time:** {session.start_time.isoformat()}")
        lines.append(f"- **End Time:** {session.end_time.isoformat()}")
        lines.append(f"- **Duration:** {session.duration}")
        lines.append("")

        # Usage Statistics
        lines.append("## Usage Statistics")
        lines.append("")
        lines.append(f"- **Total Events:** {metrics.total_events}")
        lines.append(f"- **Model Turns:** {metrics.model_turns}")
        lines.append(f"- **Tool Calls:** {metrics.tool_calls}")
        lines.append(f"- **Sub-agents Invoked:** {metrics.sub_agents_invoked}")
        lines.append(f"- **Errors:** {metrics.errors}")
        lines.append("")

        # Billing Reference
        if pricing_config:
            lines.append("## Billing Reference")
            lines.append("")
            lines.append("**Pricing Configuration:**")
            lines.append("")
            lines.append(f"- **Plan Type:** {pricing_config.plan_type}")
            lines.append(f"- **Included Credits:** {pricing_config.included_credits_per_month:,} credits/month")
            lines.append(f"- **Credit Rate:** ${pricing_config.credit_to_usd_rate:.2f} USD per credit (1 credit = ${pricing_config.credit_to_usd_rate:.2f} USD)")
            lines.append("")
            lines.append("**Reference:**")
            lines.append("- [GitHub Copilot Models and Pricing](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)")
            lines.append("- [GitHub Enterprise Cloud Models and Pricing](https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-billing/models-and-pricing)")
            lines.append("")
            lines.append("*Note: GitHub documentation shows multipliers, not absolute USD prices. The prices below are estimates based on public API pricing and are subject to change.*")
            lines.append("")
            
            if pricing_config.model_pricing:
                lines.append("**Model Pricing Rates (per million tokens - estimated):**")
                lines.append("")
                lines.append("*Note: Pricing structures differ by provider - see tables below.*")
                lines.append("")
                
                # OpenAI models table
                openai_models = pricing_config.model_pricing.get("openai", {})
                if openai_models:
                    lines.append("**OpenAI Models**")
                    lines.append("")
                    lines.append("*OpenAI uses a single cached token cost.*")
                    lines.append("")
                    lines.append("| Model | Input (USD) | Output (USD) | Cached (USD) |")
                    lines.append("|-------|-------------|--------------|--------------|")
                    for model_name, pricing in sorted(openai_models.items()):
                        lines.append(
                            f"| {model_name} | ${pricing.input_per_million:.2f} | ${pricing.output_per_million:.2f} | ${pricing.cached_read_per_million:.2f} |"
                        )
                    lines.append("")
                
                # Anthropic models table
                anthropic_models = pricing_config.model_pricing.get("anthropic", {})
                if anthropic_models:
                    lines.append("**Anthropic Models**")
                    lines.append("")
                    lines.append("*Anthropic has separate cache read and cache write costs.*")
                    lines.append("")
                    lines.append("| Model | Input (USD) | Output (USD) | Cached Read (USD) | Cached Write (USD) |")
                    lines.append("|-------|-------------|--------------|-------------------|--------------------|")
                    for model_name, pricing in sorted(anthropic_models.items()):
                        lines.append(
                            f"| {model_name} | ${pricing.input_per_million:.2f} | ${pricing.output_per_million:.2f} | ${pricing.cached_read_per_million:.2f} | ${pricing.cached_write_per_million:.2f} |"
                        )
                    lines.append("")
            
            lines.append("**Cost Calculation Formula:**")
            lines.append("")
            lines.append("*Note: Cost calculation differs by provider due to different cached token pricing structures.*")
            lines.append("")
            lines.append("**OpenAI models (single cached cost):**")
            lines.append("")
            lines.append("``")
            lines.append("Cost = (Input Tokens / 1,000,000) × Input Price")
            lines.append("     + (Output Tokens / 1,000,000) × Output Price")
            lines.append("     + (Cached Tokens / 1,000,000) × Cached Price")
            lines.append("``")
            lines.append("")
            lines.append("**Anthropic models (separate cache read/write costs):**")
            lines.append("")
            lines.append("``")
            lines.append("Cost = (Input Tokens / 1,000,000) × Input Price")
            lines.append("     + (Output Tokens / 1,000,000) × Output Price")
            lines.append("     + (Cached Read Tokens / 1,000,000) × Cached Read Price")
            lines.append("     + (Cached Write Tokens / 1,000,000) × Cached Write Price")
            lines.append("``")
            lines.append("")
            lines.append("*Note: Log data does not distinguish between cached read and cached write tokens. For Anthropic models, a cost range is shown: lower bound assumes all cached tokens are reads, upper bound assumes all cached tokens incur both read and write costs.*")
            lines.append("")
            lines.append("**Credits Calculation:**")
            lines.append("")
            lines.append("``")
            lines.append("Credits = Total Cost (USD) / Credit Rate")
            lines.append(f"Example: ${total_cost_usd:.4f} USD / ${pricing_config.credit_to_usd_rate:.2f} = {total_credits} credits")
            lines.append("``")
            lines.append("")

        # Context Overhead Analysis
        if context_overhead:
            lines.append("## Context Budget Breakdown")
            lines.append("")
            otel_limited = (context_overhead.system_prompt_tokens_est == 0
                            and context_overhead.custom_instructions_tokens_est == 0)
            if otel_limited:
                lines.append("> *Source: Copilot CLI OTel export. System prompt and custom instructions data are not captured in this format — only tool definitions and LLM token counts are available.*")
            else:
                lines.append("> *Estimates are based on character count ÷ 4 approximation. Actual token counts may vary slightly.*")
            lines.append("")
            avg = context_overhead.avg_prompt_tokens
            sys_t = context_overhead.system_prompt_tokens_est
            ci_t = context_overhead.custom_instructions_tokens_est
            builtin_t = context_overhead.builtin_tool_tokens_est
            mcp_t = context_overhead.mcp_tool_tokens_est
            act_t = context_overhead.activator_tool_tokens_est
            total_overhead = context_overhead.total_overhead_tokens_est
            conversation_t = max(0, avg - total_overhead)

            def pct(v, total):
                return f"{v / total * 100:.1f}%" if total else "0%"

            lines.append("| Component | Tokens (est.) | % of Avg Prompt |")
            lines.append("|-----------|--------------|-----------------|")
            if not otel_limited:
                lines.append(f"| System Prompt (base) | {sys_t:,} | {pct(sys_t, avg)} |")
                lines.append(f"| Custom Instructions | {ci_t:,} | {pct(ci_t, avg)} |")
            else:
                lines.append(f"| System Prompt (base) | *n/a* | *n/a* |")
                lines.append(f"| Custom Instructions | *n/a* | *n/a* |")
            lines.append(f"| Tool Definitions — Built-in ({len([t for t in context_overhead.registered_tools if t.category == 'builtin'])}) | {builtin_t:,} | {pct(builtin_t, avg)} |")
            lines.append(f"| Tool Definitions — MCP ({len([t for t in context_overhead.registered_tools if t.category == 'mcp'])}) | {mcp_t:,} | {pct(mcp_t, avg)} |")
            lines.append(f"| Tool Definitions — Activators ({len([t for t in context_overhead.registered_tools if t.category == 'activator'])}) | {act_t:,} | {pct(act_t, avg)} |")
            lines.append(f"| **Total Overhead** | **{total_overhead:,}** | **{pct(total_overhead, avg)}** |")
            lines.append(f"| Conversation History (net) | ~{conversation_t:,} | ~{pct(conversation_t, avg)} |")
            lines.append(f"| **Average Prompt Total** | **{avg:,}** | 100% |")
            lines.append("")

            if context_overhead.mcp_never_invoked_tokens_est > 0:
                savings_total = context_overhead.potential_savings_tokens
                lines.append(f"> **Optimization Opportunity:** {len(context_overhead.mcp_tools_never_invoked)} MCP tools were registered but never invoked, contributing ~{context_overhead.mcp_never_invoked_tokens_est:,} tokens of overhead per request.")
                lines.append(f"> Removing them could save approximately **{savings_total:,} tokens** across this session's {context_overhead.total_requests} requests.")
                lines.append("")

        # Tool Availability vs Usage
        if context_overhead and context_overhead.registered_tools:
            lines.append("## Tool Availability vs Usage")
            lines.append("")
            lines.append(f"**{len(context_overhead.registered_tools)} tools registered** in context | **{sum(1 for t in context_overhead.registered_tools if t.was_invoked)} tools actually invoked**")
            lines.append("")

            by_cat = context_overhead.tools_by_category
            for cat_label, cat_key in [("Built-in Tools", "builtin"), ("MCP Tools", "mcp"), ("Activator Tools", "activator")]:
                tools_in_cat = by_cat.get(cat_key, [])
                if not tools_in_cat:
                    continue
                invoked = [t for t in tools_in_cat if t.was_invoked]
                not_invoked = [t for t in tools_in_cat if not t.was_invoked]
                cat_tokens = sum(t.definition_tokens_est for t in tools_in_cat)
                lines.append(f"### {cat_label} ({len(tools_in_cat)} registered, {len(invoked)} used, ~{cat_tokens:,} tokens overhead/request)")
                lines.append("")
                lines.append("| Tool | Used | Invocations | Tokens (est.) |")
                lines.append("|------|------|-------------|---------------|")
                for t in sorted(tools_in_cat, key=lambda x: (-x.invocation_count, x.name)):
                    used_icon = "✅" if t.was_invoked else "❌"
                    mcp_note = f" `{t.mcp_server}`" if t.mcp_server else ""
                    lines.append(f"| `{t.name}`{mcp_note} | {used_icon} | {t.invocation_count} | ~{t.definition_tokens_est:,} |")
                lines.append("")

            if context_overhead.mcp_tools_never_invoked:
                lines.append("**Recommendation:** Consider disabling the following MCP servers/tools that were never used in this session — they add context overhead without benefit:")
                lines.append("")
                mcp_servers_unused = sorted(set(
                    t.mcp_server for t in context_overhead.mcp_tools_never_invoked if t.mcp_server
                ))
                for server in mcp_servers_unused:
                    server_tools = [t for t in context_overhead.mcp_tools_never_invoked if t.mcp_server == server]
                    server_tokens = sum(t.definition_tokens_est for t in server_tools)
                    lines.append(f"- **`{server}`** — {len(server_tools)} tools, ~{server_tokens:,} tokens overhead/request")
                lines.append("")

        # Token Analysis
        lines.append("## Token Analysis")
        lines.append("")
        lines.append(f"- **Input Tokens:** {metrics.total_tokens_input:,}")
        lines.append(f"- **Output Tokens:** {metrics.total_tokens_output:,}")
        if metrics.total_reasoning_tokens:
            lines.append(f"  - **↳ Reasoning (thinking) Tokens:** {metrics.total_reasoning_tokens:,} *(subset of output, billed as output)*")
        lines.append(f"- **Cached Tokens:** {metrics.total_tokens_cached:,}")
        lines.append(f"- **Total Tokens:** {metrics.total_tokens_input + metrics.total_tokens_output + metrics.total_tokens_cached:,}")
        lines.append("")

        if config.include_charts and model_usage:
            lines.append("### Token Usage by Model")
            lines.append("")
            model_tokens = {m.model_name: m.total_tokens for m in model_usage}
            chart_path = self.chart_generator.generate_bar_chart(
                model_tokens, "Token Usage by Model", "Model", "Tokens"
            )
            lines.append(f"![Token Usage by Model]({chart_path})")
            lines.append("")

        # Model Performance
        if model_usage:
            lines.append("## Model Performance")
            lines.append("")
            has_reasoning = any(m.total_reasoning_tokens > 0 for m in model_usage)
            if has_reasoning:
                lines.append("| Model | Provider | Input Tokens | Output Tokens | Reasoning Tokens | Cached Tokens | Requests | Cost (USD) |")
                lines.append("|-------|----------|--------------|---------------|------------------|---------------|----------|------------|")
            else:
                lines.append("| Model | Provider | Input Tokens | Output Tokens | Cached Tokens | Requests | Cost (USD) |")
                lines.append("|-------|----------|--------------|---------------|---------------|----------|------------|")
            for m in model_usage:
                if has_reasoning:
                    reasoning_col = f"{m.total_reasoning_tokens:,}" if m.total_reasoning_tokens else "-"
                # For Anthropic models, show a cost range since we can't distinguish
                # between cached read and cached write tokens in the log data
                if pricing_config and m.provider.lower() == "anthropic":
                    model_pricing = pricing_config.model_pricing.get(m.provider, {}).get(m.model_name)
                    if model_pricing and m.total_cached_tokens > 0:
                        input_cost = (m.total_input_tokens / 1_000_000) * model_pricing.input_per_million
                        output_cost = (m.total_output_tokens / 1_000_000) * model_pricing.output_per_million
                        cached_read_cost = (m.total_cached_tokens / 1_000_000) * model_pricing.cached_read_per_million
                        cached_write_cost = (m.total_cached_tokens / 1_000_000) * model_pricing.cached_write_per_million
                        min_cost = input_cost + output_cost + cached_read_cost
                        max_cost = input_cost + output_cost + cached_read_cost + cached_write_cost
                        cost_display = f"${min_cost:.4f} - ${max_cost:.4f}"
                    else:
                        cost_display = f"${m.estimated_cost_usd:.4f}"
                else:
                    cost_display = f"${m.estimated_cost_usd:.4f}"

                if has_reasoning:
                    lines.append(
                        f"| {m.model_name} | {m.provider} | {m.total_input_tokens:,} | {m.total_output_tokens:,} | {reasoning_col} | {m.total_cached_tokens:,} | {m.total_requests} | {cost_display} |"
                    )
                else:
                    lines.append(
                        f"| {m.model_name} | {m.provider} | {m.total_input_tokens:,} | {m.total_output_tokens:,} | {m.total_cached_tokens:,} | {m.total_requests} | {cost_display} |"
                    )
            lines.append("")
            lines.append("*Note: Anthropic models show a cost range because log data does not distinguish between cached read and cached write tokens. Lower bound = all cached tokens are reads only. Upper bound = all cached tokens incur both read and write costs.*")
            lines.append("")

        # Tool Usage
        if tool_usage:
            lines.append("## Tool Usage")
            lines.append("")
            lines.append("| Tool | Invocations | Success | Failure | Avg Duration (ms) | Success Rate |")
            lines.append("|------|-------------|---------|---------|-------------------|--------------|")
            for t in tool_usage:
                lines.append(
                    f"| {t.tool_name} | {t.invocation_count} | {t.success_count} | {t.failure_count} | {t.average_duration_ms:.2f} | {t.success_rate:.1%} |"
                )
            lines.append("")

            if config.include_charts:
                tool_counts = {t.tool_name: t.invocation_count for t in tool_usage}
                chart_path = self.chart_generator.generate_bar_chart(
                    tool_counts, "Tool Invocation Counts", "Tool", "Count"
                )
                lines.append(f"![Tool Invocation Counts]({chart_path})")
                lines.append("")

        # Hotspot Analysis
        if hotspots:
            lines.append("## Hotspot Analysis")
            lines.append("")
            lines.append(f"**{len(hotspots)} hotspots detected**")
            lines.append("")
            lines.append("| Severity | Type | Description | Task | Model |")
            lines.append("|----------|------|-------------|------|-------|")
            for h in hotspots:
                lines.append(
                    f"| {h.severity.value} | {h.hotspot_type.value} | {h.description} | {h.task_description or 'N/A'} | {h.model_used or 'N/A'} |"
                )
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        if hotspots:
            lines.append("Based on the analysis, consider the following optimizations:")
            lines.append("")
            for hotspot in hotspots[:5]:
                lines.append(f"- **{hotspot.hotspot_type.value}:** {hotspot.description}")
                if hotspot.severity == HotspotSeverity.HIGH:
                    lines.append("  - Priority: HIGH - Address this issue first")
            lines.append("")
        else:
            lines.append("No significant issues detected. Your usage appears to be efficient.")
            lines.append("")

        return "\n".join(lines)
