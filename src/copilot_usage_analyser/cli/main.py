"""Main CLI entry point."""

import click
from rich.console import Console

from ..application.use_cases import AnalyzeSession, GenerateReport, ReportConfig
from ..domain.services import CostCalculator, HotspotDetector, MetricsCalculator
from ..domain.value_objects import PricingConfig
from ..infrastructure.adapters import OTLPAdapter
from ..infrastructure.charts import ChartGenerator
from ..infrastructure.readers import LogFileReader

console = Console()


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
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def analyze(file, output, type, format, plan, config, no_charts, verbose):
    """Analyze a Copilot debug log file and generate a report."""
    if verbose:
        console.print(f"[bold blue]Analyzing file:[/bold blue] {file}")

    # Initialize components
    file_reader = LogFileReader()
    otlp_adapter = OTLPAdapter()
    metrics_calculator = MetricsCalculator()
    hotspot_detector = HotspotDetector()

    # Load pricing config
    pricing_config = PricingConfig(
        plan_type=plan,
        included_credits_per_month=1900 if plan == "business" else 5000,
        credit_to_usd_rate=0.01,
    )

    cost_calculator = CostCalculator(pricing_config)

    # Set up chart generator
    output_dir = output or "reports"
    chart_generator = ChartGenerator(output_dir)

    # Analyze session
    analyze_use_case = AnalyzeSession(
        file_reader=file_reader,
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
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def batch(directory, output, plan, no_charts, verbose):
    """Batch analyze all log files in a directory."""
    console.print(f"[bold blue]Batch analyzing directory:[/bold blue] {directory}")

    import os

    log_files = [
        f for f in os.listdir(directory) if f.endswith((".json", ".jsonl"))
    ]

    if not log_files:
        console.print("[yellow]No log files found in directory[/yellow]")
        return

    console.print(f"Found {len(log_files)} log files")

    for log_file in log_files:
        file_path = os.path.join(directory, log_file)
        console.print(f"\n[bold]Processing:[/bold] {log_file}")

        try:
            analyze.callback(
                file=file_path,
                output=output,
                type="detailed",
                format="markdown",
                plan=plan,
                config=None,
                no_charts=no_charts,
                verbose=verbose,
            )
        except Exception as e:
            console.print(f"[bold red]Error processing {log_file}:[/bold red] {e}")

    console.print(f"\n[bold green]✓[/bold green] Batch analysis complete")


if __name__ == "__main__":
    cli()
