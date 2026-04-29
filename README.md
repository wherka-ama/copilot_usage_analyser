# Copilot Usage Analyzer

A command-line tool to analyze GitHub Copilot Agent Debug Logs and generate comprehensive usage reports with insights and recommendations.

## Features

- **Parse Copilot Debug Logs**: Process OTLP JSON/JSONL format logs exported from VS Code Agent Debug panel
- **Token Analysis**: Detailed breakdown of input, output, and cached tokens with cost estimation
- **Tool Usage**: Analyze tool invocation patterns and efficiency
- **Hotspot Detection**: Identify anomalous usage patterns and optimization opportunities
- **Report Generation**: Generate markdown reports with embedded charts
- **Cost Estimation**: Calculate AI credits and USD costs based on plan type
- **Multiple Report Types**: Executive, summary, and detailed reports

## Installation

### From PyPI (when published)
```bash
pip install copilot-usage-analyser
```

### From Source
```bash
git clone https://github.com/yourusername/copilot-usage-analyser
cd copilot-usage-analyser
pip install -e .
```

### Development Installation
```bash
pip install -e ".[dev]"
```

## Quick Start

### Analyze a Single Session
```bash
cua analyze session.jsonl
```

### Generate Executive Report
```bash
cua analyze --type executive session.jsonl
```

### Batch Analyze Directory
```bash
cua analyze --batch logs/
```

### Custom Configuration
```bash
cua analyze --config custom.yaml session.jsonl
```

## Usage

### Command-Line Interface

```bash
cua analyze [OPTIONS] FILE

Options:
  -o, --output PATH              Output file/directory
  -t, --type [executive|summary|detailed]
                                Report type (default: detailed)
  -f, --format [markdown|html]  Output format (default: markdown)
  -p, --plan [business|enterprise|individual]
                                Plan type (default: business)
  -c, --config PATH              Configuration file
  --no-charts                    Disable chart generation
  --include-raw-data            Include raw event data
  -v, --verbose                  Verbose output
  -h, --help                     Show help
```

### Configuration

Create a configuration file in `~/.cua/config.yaml`:

```yaml
plan_type: business
hotspot_threshold_std_dev: 2.0
include_charts: true
chart_format: png
```

### Pricing Configuration

Custom pricing can be configured in `config/pricing/`:

```yaml
plan_type: business
included_credits_per_month: 1900
credit_to_usd_rate: 0.01
model_pricing:
  openai:
    gpt-4:
      input_per_million: 30
      output_per_million: 60
```

## Exporting Debug Logs

1. Enable Agent Debug Logs in VS Code:
   - Set `github.copilot.chat.agentDebugLog.enabled` to `true`
   - Set `github.copilot.chat.agentDebugLog.fileLogging.enabled` to `true`

2. Open the Agent Debug panel:
   - Click the ellipsis (...) menu in Chat view
   - Select "Show Agent Debug Logs"

3. Export the session:
   - Click the Export icon (download)
   - Save the JSON file

4. Analyze the exported file:
   ```bash
   cua analyze exported-session.jsonl
   ```

## Report Structure

Generated reports include:

1. **Executive Summary**: High-level overview and key findings
2. **Session Overview**: Basic session metadata and timeline
3. **Usage Statistics**: Detailed metrics and statistics
4. **Token Analysis**: Token usage breakdown and cost analysis
5. **Tool Usage**: Tool invocation patterns and efficiency
6. **Temporal Analysis**: Usage patterns over time
7. **Hotspot Analysis**: Anomalous usage patterns and recommendations
8. **Model Performance**: Model-specific analysis
9. **Recommendations**: Actionable insights and optimization suggestions

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black src/ tests/
```

### Linting
```bash
ruff check src/ tests/
```

### Type Checking
```bash
mypy src/
```

## Architecture

The tool follows hexagonal architecture principles:

- **Domain Layer**: Core business entities and services
- **Application Layer**: Use cases and orchestration
- **Infrastructure Layer**: File I/O, adapters, and chart generation
- **Interface Layer**: CLI and library API

See [docs/05-technical-specification.md](docs/05-technical-specification.md) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- GitHub Copilot team for the Agent Debug Log feature
- OpenTelemetry for the log format standard
