"""Main CLI entry point."""

import click
from rich.console import Console

from copilot_usage_analyser.application.use_cases import AnalyzeSession, ExportCSV, GenerateReport, ReportConfig
from copilot_usage_analyser.domain.services import CostCalculator, HotspotDetector, MetricsCalculator
from copilot_usage_analyser.domain.value_objects import PricingConfig
from copilot_usage_analyser.infrastructure.adapters import ChatReplayAdapter, OTLPAdapter
from copilot_usage_analyser.infrastructure.charts import ChartGenerator
from copilot_usage_analyser.infrastructure.readers import LogFileReader

console = Console()


def _merge_overhead_stats(stats_list):
    """Merge ContextOverheadStats from multiple files into a single aggregated view."""
    from copilot_usage_analyser.domain.entities import ContextOverheadStats, ToolRegistrationInfo

    if not stats_list:
        return None
    if len(stats_list) == 1:
        return stats_list[0]

    # Aggregate invocation counts across all files
    merged_invocations = {}
    for stats in stats_list:
        for tool in stats.registered_tools:
            merged_invocations[tool.name] = merged_invocations.get(tool.name, 0) + tool.invocation_count

    # Use tool definitions from the file with the most tools registered
    base = max(stats_list, key=lambda s: len(s.registered_tools))

    merged_tools = [
        ToolRegistrationInfo(
            name=t.name,
            category=t.category,
            mcp_server=t.mcp_server,
            definition_tokens_est=t.definition_tokens_est,
            invocation_count=merged_invocations.get(t.name, 0),
        )
        for t in base.registered_tools
    ]

    total_requests = sum(s.total_requests for s in stats_list)
    avg_prompt = sum(s.avg_prompt_tokens * s.total_requests for s in stats_list) // max(total_requests, 1)

    return ContextOverheadStats(
        total_requests=total_requests,
        avg_prompt_tokens=avg_prompt,
        system_prompt_tokens_est=base.system_prompt_tokens_est,
        custom_instructions_tokens_est=base.custom_instructions_tokens_est,
        builtin_tool_tokens_est=base.builtin_tool_tokens_est,
        mcp_tool_tokens_est=base.mcp_tool_tokens_est,
        activator_tool_tokens_est=base.activator_tool_tokens_est,
        registered_tools=merged_tools,
    )


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Copilot Usage Analyzer - Analyze GitHub Copilot Agent Debug Logs."""
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file/directory",
)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["executive", "summary", "detailed"]),
    default="detailed",
    help="Report type",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["markdown", "html"]),
    default="markdown",
    help="Output format",
)
@click.option(
    "-p",
    "--plan",
    type=click.Choice(["business", "enterprise", "individual"]),
    default="business",
    help="Plan type for pricing",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True),
    help="Configuration file",
)
@click.option(
    "--no-charts",
    is_flag=True,
    help="Disable chart generation",
)
@click.option(
    "--csv",
    is_flag=True,
    help="Export detailed token usage to CSV file",
)
@click.option(
    "--timeline",
    is_flag=True,
    help="Generate timeline chart showing token usage over time",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def analyze(file, output, type, format, plan, config, no_charts, csv, timeline, verbose):
    """Analyze a Copilot debug log file and generate a report."""
    if verbose:
        console.print(f"[bold blue]Analyzing file:[/bold blue] {file}")

    # Initialize components
    file_reader = LogFileReader()
    chatreplay_adapter = ChatReplayAdapter()
    otlp_adapter = OTLPAdapter()
    metrics_calculator = MetricsCalculator()
    hotspot_detector = HotspotDetector()

    # Load pricing config (TODO: Use YAML config loader when package data is properly configured)
    from ..domain.value_objects import ModelPricing
    
    pricing_config = PricingConfig(
        plan_type=plan,
        included_credits_per_month=1900 if plan == "business" else 5000,
        credit_to_usd_rate=0.01,
        model_pricing={
            "openai": {
                "gpt-4o-mini": ModelPricing(
                    input_per_million=0.5,
                    output_per_million=1.5,
                    cached_read_per_million=0.1,
                    cached_write_per_million=0.5,
                ),
                "gpt-4": ModelPricing(
                    input_per_million=30.0,
                    output_per_million=60.0,
                    cached_read_per_million=0.1,
                    cached_write_per_million=30.0,
                ),
                "gpt-4-turbo": ModelPricing(
                    input_per_million=10.0,
                    output_per_million=30.0,
                    cached_read_per_million=0.1,
                    cached_write_per_million=10.0,
                ),
            },
            "anthropic": {
                "claude-opus-4.6": ModelPricing(
                    input_per_million=5.00,
                    output_per_million=25.00,
                    cached_read_per_million=0.50,
                    cached_write_per_million=6.25,
                ),
                "claude-sonnet-4.6": ModelPricing(
                    input_per_million=3.00,
                    output_per_million=15.00,
                    cached_read_per_million=0.30,
                    cached_write_per_million=3.75,
                ),
                "claude-sonnet-4": ModelPricing(
                    input_per_million=3.00,
                    output_per_million=15.00,
                    cached_read_per_million=0.30,
                    cached_write_per_million=3.75,
                ),
                "claude-3.5-sonnet": ModelPricing(
                    input_per_million=3.00,
                    output_per_million=15.00,
                    cached_read_per_million=0.30,
                    cached_write_per_million=3.75,
                ),
            },
        },
    )

    cost_calculator = CostCalculator(pricing_config)

    # Set up chart generator
    output_dir = output or "reports"
    chart_generator = ChartGenerator(output_dir)

    # Analyze session
    analyze_use_case = AnalyzeSession(
        file_reader=file_reader,
        chatreplay_adapter=chatreplay_adapter,
        otlp_adapter=otlp_adapter,
        metrics_calculator=metrics_calculator,
        cost_calculator=cost_calculator,
        hotspot_detector=hotspot_detector,
    )

    try:
        with console.status("[bold green]Analyzing session..."):
            parsed_session = analyze_use_case.execute(file)

        if verbose:
            console.print(f"[bold green]✓[/bold green] Session analyzed successfully")
            console.print(f"  - Events: {parsed_session.metrics.total_events}")
            console.print(f"  - Cost: ${parsed_session.total_cost_usd:.2f} USD")
            console.print(f"  - Credits: {parsed_session.total_credits}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.ClickException(str(e))

    # Generate report
    report_config = ReportConfig(
        report_type=type,
        include_charts=not no_charts,
        chart_format="png",
        output_format=format,
    )

    generate_use_case = GenerateReport(chart_generator=chart_generator)

    try:
        with console.status("[bold green]Generating report..."):
            report_content = generate_use_case.execute(
                session=parsed_session.session,
                metrics=parsed_session.metrics,
                model_usage=parsed_session.model_usage,
                tool_usage=parsed_session.tool_usage,
                hotspots=parsed_session.hotspots,
                total_cost_usd=parsed_session.total_cost_usd,
                total_credits=parsed_session.total_credits,
                config=report_config,
                pricing_config=pricing_config,
                context_overhead=parsed_session.context_overhead,
            )

        # Determine output path
        if output:
            if output.endswith(".md"):
                output_path = output
            else:
                output_path = f"{output}/report.md"
        else:
            output_path = "report.md"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        console.print(f"[bold green]✓[/bold green] Report generated: {output_path}")

    except Exception as e:
        console.print(f"[bold red]Error generating report:[/bold red] {e}")
        raise click.ClickException(str(e))

    # Generate CSV export if requested
    if csv:
        export_use_case = ExportCSV(cost_calculator=cost_calculator)
        try:
            with console.status("[bold green]Generating CSV export..."):
                csv_content = export_use_case.execute(
                    session=parsed_session.session,
                    events=parsed_session.events,
                    model_usage=parsed_session.model_usage,
                    tool_usage=parsed_session.tool_usage,
                    hotspots=parsed_session.hotspots,
                    total_cost_usd=parsed_session.total_cost_usd,
                    pricing_config=pricing_config,
                    context_overhead=parsed_session.context_overhead,
                )
            
            # Determine CSV output path
            if output:
                if output.endswith(".md"):
                    csv_path = output.replace(".md", ".csv")
                else:
                    csv_path = f"{output}/token_usage.csv"
            else:
                csv_path = "token_usage.csv"
            
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(csv_content)
            
            console.print(f"[bold green]✓[/bold green] CSV export generated: {csv_path}")
        
        except Exception as e:
            console.print(f"[bold red]Error generating CSV export:[/bold red] {e}")
            raise click.ClickException(str(e))

    # Generate timeline chart if requested
    if timeline:
        try:
            with console.status("[bold green]Generating timeline chart..."):
                timeline_path = chart_generator.generate_timeline_chart(
                    events=parsed_session.events,
                    title="Token Usage Timeline",
                    filename="token_usage_timeline.png",
                )
            
            console.print(f"[bold green]✓[/bold green] Timeline chart generated: {timeline_path}")
        
        except Exception as e:
            console.print(f"[bold red]Error generating timeline chart:[/bold red] {e}")
            raise click.ClickException(str(e))


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output directory",
    default="reports",
)
@click.option(
    "-p",
    "--plan",
    type=click.Choice(["business", "enterprise", "individual"]),
    default="business",
    help="Plan type for pricing",
)
@click.option(
    "--no-charts",
    is_flag=True,
    help="Disable chart generation",
)
@click.option(
    "--csv",
    is_flag=True,
    help="Export detailed token usage to CSV file",
)
@click.option(
    "--timeline",
    is_flag=True,
    help="Generate timeline chart showing token usage over time",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def batch(directory, output, plan, no_charts, csv, timeline, verbose):
    """Batch analyze all log files in a directory and aggregate into a single report with deduplication."""
    console.print(f"[bold blue]Batch analyzing directory:[/bold blue] {directory}")

    import os

    log_files = [
        f for f in os.listdir(directory) if f.endswith((".json", ".jsonl"))
    ]

    if not log_files:
        console.print("[yellow]No log files found in directory[/yellow]")
        return

    console.print(f"Found {len(log_files)} log files")

    # Initialize components
    file_reader = LogFileReader()
    chatreplay_adapter = ChatReplayAdapter()
    otlp_adapter = OTLPAdapter()
    metrics_calculator = MetricsCalculator()
    hotspot_detector = HotspotDetector()
    chart_generator = ChartGenerator(output)

    # Load pricing config (TODO: Use YAML config loader when package data is properly configured)
    from ..domain.value_objects import ModelPricing
    
    pricing_config = PricingConfig(
        plan_type=plan,
        included_credits_per_month=1900 if plan == "business" else 5000,
        credit_to_usd_rate=0.01,
        model_pricing={
            "openai": {
                "gpt-4o-mini": ModelPricing(
                    input_per_million=0.5,
                    output_per_million=1.5,
                    cached_read_per_million=0.1,
                    cached_write_per_million=0.5,
                ),
                "gpt-4": ModelPricing(
                    input_per_million=30.0,
                    output_per_million=60.0,
                    cached_read_per_million=0.1,
                    cached_write_per_million=30.0,
                ),
                "gpt-4-turbo": ModelPricing(
                    input_per_million=10.0,
                    output_per_million=30.0,
                    cached_read_per_million=0.1,
                    cached_write_per_million=10.0,
                ),
            },
            "anthropic": {
                "claude-opus-4.6": ModelPricing(
                    input_per_million=5.00,
                    output_per_million=25.00,
                    cached_read_per_million=0.50,
                    cached_write_per_million=6.25,
                ),
                "claude-sonnet-4.6": ModelPricing(
                    input_per_million=3.00,
                    output_per_million=15.00,
                    cached_read_per_million=0.30,
                    cached_write_per_million=3.75,
                ),
                "claude-sonnet-4": ModelPricing(
                    input_per_million=3.00,
                    output_per_million=15.00,
                    cached_read_per_million=0.30,
                    cached_write_per_million=3.75,
                ),
                "claude-3.5-sonnet": ModelPricing(
                    input_per_million=3.00,
                    output_per_million=15.00,
                    cached_read_per_million=0.30,
                    cached_write_per_million=3.75,
                ),
            },
        },
    )
    
    cost_calculator = CostCalculator(pricing_config)

    # Aggregate all events from all files
    all_events = []
    all_sessions = []
    all_overhead_stats = []
    seen_event_ids = set()

    for log_file in log_files:
        file_path = os.path.join(directory, log_file)
        console.print(f"\n[bold]Processing:[/bold] {log_file}")

        try:
            # Detect format and use appropriate adapter
            format_type = file_reader.detect_format(file_path)
            
            # Read file
            log_data = file_reader.read_file(file_path)
            
            if format_type == "chatreplay":
                session, events = chatreplay_adapter.adapt(log_data)
                overhead = chatreplay_adapter.extract_overhead_data(log_data)
                if overhead:
                    all_overhead_stats.append(overhead)
            elif format_type == "otlp":
                session, events = otlp_adapter.adapt(log_data)
            else:
                console.print(f"[yellow]Unknown format for {log_file}, skipping[/yellow]")
                continue

            # Deduplicate events by event_id
            for event in events:
                if event.event_id not in seen_event_ids:
                    seen_event_ids.add(event.event_id)
                    all_events.append(event)

            all_sessions.append(session)
            console.print(f"[green]✓[/green] Processed {len(events)} events ({len([e for e in events if e.event_id not in seen_event_ids])} new)")

        except Exception as e:
            console.print(f"[bold red]Error processing {log_file}:[/bold red] {e}")
            if verbose:
                import traceback
                console.print(traceback.format_exc())

    if not all_events:
        console.print("[yellow]No events found after processing all files[/yellow]")
        return

    console.print(f"\n[bold green]Aggregated {len(all_events)} unique events from {len(all_sessions)} files[/bold green]")

    # Create aggregated session
    from ..domain.entities import Session, AgentType, PlanType
    from datetime import datetime
    
    # Calculate overall session bounds
    start_time = min(s.start_time for s in all_sessions)
    end_time = max(s.end_time for s in all_sessions)
    duration = end_time - start_time

    aggregated_session = Session(
        session_id="batch-aggregated",
        title=f"Batch Analysis ({len(all_sessions)} files)",
        agent_type=AgentType.VSCODE,
        model="mixed",
        plan_type=PlanType.BUSINESS if plan == "business" else PlanType.ENTERPRISE,
        start_time=start_time,
        end_time=end_time,
    )

    # Calculate metrics
    session_metrics = metrics_calculator.calculate_session_metrics(all_events, aggregated_session)
    model_usage = metrics_calculator.calculate_token_usage_by_model(all_events)
    tool_usage = metrics_calculator.calculate_tool_usage(all_events)
    
    # Update model usage with costs
    cost_calculator = CostCalculator(pricing_config)
    model_usage = cost_calculator.update_model_costs(model_usage)
    
    # Calculate total cost
    total_cost_usd = cost_calculator.calculate_session_cost(all_events)
    total_credits = int(total_cost_usd / pricing_config.credit_to_usd_rate)

    # Detect hotspots
    hotspots = hotspot_detector.detect_hotspots(all_events)

    # Generate report
    generate_use_case = GenerateReport(chart_generator=chart_generator)
    report_config = ReportConfig(
        report_type="detailed",
        include_charts=not no_charts,
        chart_format="png",
        output_format="markdown",
    )

    # Merge overhead stats from all files
    merged_overhead = _merge_overhead_stats(all_overhead_stats) if all_overhead_stats else None

    report_content = generate_use_case.execute(
        session=aggregated_session,
        metrics=session_metrics,
        model_usage=model_usage,
        tool_usage=tool_usage,
        hotspots=hotspots,
        total_cost_usd=total_cost_usd,
        total_credits=total_credits,
        config=report_config,
        pricing_config=pricing_config,
        context_overhead=merged_overhead,
    )

    # Write report
    output_path = os.path.join(output, "report.md")
    os.makedirs(output, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    console.print(f"\n[bold green]✓[/bold green] Batch analysis complete")
    console.print(f"[bold green]✓[/bold green] Report generated: {output_path}")
    console.print(f"[bold]Total unique events:[/bold] {len(all_events)}")
    console.print(f"[bold]Total cost:[/bold] ${total_cost_usd:.4f} USD ({total_credits} credits)")

    # Generate CSV export if requested
    if csv:
        export_use_case = ExportCSV(cost_calculator=cost_calculator)
        try:
            with console.status("[bold green]Generating CSV export..."):
                csv_content = export_use_case.execute(
                    session=aggregated_session,
                    events=all_events,
                    model_usage=model_usage,
                    tool_usage=tool_usage,
                    hotspots=hotspots,
                    total_cost_usd=total_cost_usd,
                    pricing_config=pricing_config,
                    context_overhead=merged_overhead,
                )
            
            csv_path = os.path.join(output, "token_usage.csv")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(csv_content)
            
            console.print(f"[bold green]✓[/bold green] CSV export generated: {csv_path}")
        
        except Exception as e:
            console.print(f"[bold red]Error generating CSV export:[/bold red] {e}")
            if verbose:
                import traceback
                console.print(traceback.format_exc())

    # Generate timeline chart if requested
    if timeline:
        try:
            with console.status("[bold green]Generating timeline chart..."):
                timeline_path = chart_generator.generate_timeline_chart(
                    events=all_events,
                    title="Token Usage Timeline",
                    filename="token_usage_timeline.png",
                )
            
            console.print(f"[bold green]✓[/bold green] Timeline chart generated: {timeline_path}")
        
        except Exception as e:
            console.print(f"[bold red]Error generating timeline chart:[/bold red] {e}")
            if verbose:
                import traceback
                console.print(traceback.format_exc())


if __name__ == "__main__":
    cli()
