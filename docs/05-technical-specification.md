# Technical Specification

## Technology Stack

### Language
- **Python 3.9+**: Chosen for:
  - Minimal dependencies (standard library rich)
  - Excellent data processing libraries
  - Strong ecosystem for scientific computing
  - Easy to maintain and extend
  - Cross-platform compatibility

### Core Dependencies
```python
# Data processing
pydantic>=2.0          # Data validation and settings management
python-dateutil>=2.8   # Date/time parsing

# Chart generation
matplotlib>=3.7        # Static chart generation (PNG/SVG)
plotly>=5.0           # Interactive charts (HTML, optional)

# CLI
click>=8.0            # CLI framework
rich>=13.0            # Terminal formatting and progress bars

# Testing
pytest>=7.0           # Testing framework
pytest-cov>=4.0       # Coverage reporting
pytest-mock>=3.10     # Mocking support

# Code quality
black>=23.0           # Code formatting
ruff>=0.1.0          # Linting
mypy>=1.5            # Type checking
```

### Optional Dependencies
```python
# Additional output formats
weasyprint>=59.0      # PDF generation (optional)
jinja2>=3.1           # Template engine for HTML (optional)

# Performance
polars>=0.19          # Fast dataframes for large datasets (optional)
```

## Architecture

### Hexagonal Architecture Pattern
The system follows hexagonal (ports and adapters) architecture to ensure clean separation of concerns and testability.

```
┌─────────────────────────────────────────────────────────────┐
│                      Interface Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CLI Module │  │   API Module │  │  Library API │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Use Cases  │  │  Orchestrator│  │  Config Mgr  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Entities   │  │   Services   │  │   Value Obj  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ File Readers │  │  OTLP Adapter│  │Chart Generator│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### Interface Layer
- **CLI Module**: Command-line interface using Click
- **API Module**: REST API endpoints (future)
- **Library API**: Python library interface for programmatic use

#### Application Layer
- **Use Cases**: Business logic orchestration
- **Orchestrator**: Coordinates between domain and infrastructure
- **Config Manager**: Configuration loading and validation

#### Domain Layer
- **Entities**: Core business objects (Session, Event, Metrics)
- **Services**: Domain logic (MetricsCalculator, CostCalculator)
- **Value Objects**: Immutable data structures

#### Infrastructure Layer
- **File Readers**: File I/O operations
- **OTLP Adapter**: Format-specific transformations
- **Chart Generator**: Visualization creation

## Project Structure

```
copilot_usage_analyser/
├── src/
│   └── copilot_usage_analyser/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py           # CLI entry point
│       │   └── commands.py       # CLI command definitions
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── session.py    # Session entity
│       │   │   ├── event.py      # Event entity
│       │   │   └── metrics.py    # Metrics entity
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── metrics_calculator.py
│       │   │   ├── cost_calculator.py
│       │   │   └── hotspot_detector.py
│       │   └── value_objects/
│       │       ├── __init__.py
│       │       ├── token_usage.py
│       │       └── pricing_config.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── use_cases/
│       │   │   ├── __init__.py
│       │   │   ├── analyze_session.py
│       │   │   └── generate_report.py
│       │   ├── orchestrator.py
│       │   └── config_manager.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── readers/
│       │   │   ├── __init__.py
│       │   │   └── file_reader.py
│       │   ├── adapters/
│       │   │   ├── __init__.py
│       │   │   └── otlp_adapter.py
│       │   ├── charts/
│       │   │   ├── __init__.py
│       │   │   ├── chart_generator.py
│       │   │   └── matplotlib_generator.py
│       │   └── reports/
│       │       ├── __init__.py
│       │       ├── markdown_generator.py
│       │       └── section_generators.py
│       └── library/
│           ├── __init__.py
│           └── api.py              # Public library API
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   │   ├── test_parser_pipeline.py
│   │   └── test_report_generation.py
│   ├── fixtures/
│   │   ├── sample_logs/
│   │   └── expected_outputs/
│   └── conftest.py
├── docs/
│   ├── 01-json-schema-design.md
│   ├── 02-parser-specification.md
│   ├── 03-report-generator-specification.md
│   ├── 04-product-functional-specification.md
│   └── 05-technical-specification.md
├── config/
│   ├── default_config.yaml
│   └── pricing/
│       ├── business.yaml
│       ├── enterprise.yaml
│       └── individual.yaml
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── .gitignore
└── LICENSE
```

## Core Components

### 1. Domain Entities

#### Session Entity
```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from enum import Enum

class AgentType(Enum):
    COPILOT_CLI = "copilot_cli"
    CLAUDE_CLI = "claude_cli"
    VSCODE = "vscode"
    CLOUD = "cloud"

class PlanType(Enum):
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    INDIVIDUAL = "individual"

@dataclass
class Session:
    session_id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    agent_type: AgentType
    model: str
    plan_type: PlanType = PlanType.BUSINESS
    
    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time
```

#### Event Entity
```python
class EventType(Enum):
    MODEL_TURN = "model_turn"
    TOOL_CALL = "tool_call"
    DISCOVERY = "discovery"
    ERROR = "error"
    SUB_AGENT = "sub_agent"
    CUSTOM_AGENT = "custom_agent"

@dataclass
class TokenUsage:
    input: int = 0
    output: int = 0
    cached: int = 0
    
    @property
    def total(self) -> int:
        return self.input + self.output + self.cached

@dataclass
class Event:
    event_id: UUID
    timestamp: datetime
    event_type: EventType
    summary: str
    token_usage: TokenUsage
    duration_ms: float
    parent_event_id: Optional[UUID] = None
    agent_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
```

#### Metrics Entity
```python
@dataclass
class SessionMetrics:
    total_events: int
    model_turns: int
    tool_calls: int
    total_tokens: TokenUsage
    errors: int
    sub_agents_invoked: int
```

### 2. Domain Services

#### Metrics Calculator
```python
class MetricsCalculator:
    def calculate_session_metrics(
        self, 
        events: List[Event],
        session: Session
    ) -> SessionMetrics:
        """Calculate aggregate metrics from events"""
        
    def calculate_token_usage_by_model(
        self, 
        events: List[Event]
    ) -> List[ModelTokenUsage]:
        """Group token usage by model"""
        
    def calculate_tool_usage(
        self, 
        events: List[Event]
    ) -> List[ToolUsageStats]:
        """Calculate tool usage statistics"""
```

#### Cost Calculator
```python
class CostCalculator:
    def __init__(self, pricing_config: PricingConfig):
        self.pricing = pricing_config
        
    def calculate_cost(
        self, 
        token_usage: TokenUsage, 
        model: str
    ) -> float:
        """Calculate cost in USD"""
        
    def calculate_credits(self, cost_usd: float) -> int:
        """Convert USD to AI credits (1 credit = $0.01)"""
```

#### Hotspot Detector
```python
class HotspotDetector:
    def __init__(self, threshold_std_dev: float = 2.0):
        self.threshold = threshold_std_dev
        
    def detect_hotspots(
        self, 
        events: List[Event]
    ) -> List[Hotspot]:
        """Detect anomalous usage patterns"""
        
    def _calculate_baseline(
        self, 
        events: List[Event]
    ) -> Dict[str, BaselineMetric]:
        """Calculate baseline statistics"""
```

### 3. Application Use Cases

#### Analyze Session Use Case
```python
class AnalyzeSession:
    def __init__(
        self,
        file_reader: LogFileReader,
        otlp_adapter: OTLPAdapter,
        metrics_calculator: MetricsCalculator,
        cost_calculator: CostCalculator,
        hotspot_detector: HotspotDetector
    ):
        self.file_reader = file_reader
        self.adapter = otlp_adapter
        self.metrics_calculator = metrics_calculator
        self.cost_calculator = cost_calculator
        self.hotspot_detector = hotspot_detector
        
    def execute(
        self, 
        file_path: str,
        config: ParserConfig
    ) -> ParsedSession:
        """Parse and analyze a session log file"""
        # 1. Read file
        raw_data = self.file_reader.read_file(file_path)
        
        # 2. Adapt format
        session = self.adapter.adapt(raw_data)
        
        # 3. Calculate metrics
        metrics = self.metrics_calculator.calculate_session_metrics(
            session.events, session.session
        )
        
        # 4. Calculate costs
        costs = self.cost_calculator.calculate_total_cost(session)
        
        # 5. Detect hotspots
        hotspots = self.hotspot_detector.detect_hotspots(session.events)
        
        return ParsedSession(
            session=session,
            metrics=metrics,
            costs=costs,
            hotspots=hotspots
        )
```

### 4. Infrastructure Components

#### File Reader
```python
class LogFileReader:
    def read_file(self, file_path: str) -> Iterator[Dict]:
        """Read JSONL or JSON file and yield objects"""
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Try JSONL first
        try:
            for line in content.strip().split('\n'):
                yield json.loads(line)
        except json.JSONDecodeError:
            # Fall back to single JSON
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                yield data
```

#### OTLP Adapter
```python
class OTLPAdapter:
    def adapt(self, otlp_data: List[Dict]) -> InternalSession:
        """Transform OTLP data to internal session model"""
        resource_spans = otlp_data[0].get('resourceSpans', [])
        
        # Extract session info from resource
        resource = resource_spans[0].get('resource', {})
        session_info = self._extract_session_info(resource)
        
        # Extract events from spans
        spans = resource_spans[0].get('scopeSpans', [{}])[0].get('spans', [])
        events = [self._adapt_span(span) for span in spans]
        
        return InternalSession(
            session=session_info,
            events=events
        )
```

#### Chart Generator
```python
class ChartGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        
    def generate_pie_chart(
        self, 
        data: Dict[str, int],
        title: str
    ) -> str:
        """Generate pie chart and return path"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')
        ax.set_title(title)
        
        path = os.path.join(self.output_dir, f"{title.replace(' ', '_')}.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
```

## CLI Design

### Command Structure
```bash
cua analyze [OPTIONS] <FILE>
cua analyze --batch [OPTIONS] <DIRECTORY>
cua config init
cua config validate [CONFIG_FILE]
cua --version
cua --help
```

### Main Command: analyze
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

### Example Usage
```bash
# Analyze single session
cua analyze session.jsonl

# Generate executive report
cua analyze --type executive session.jsonl

# Batch analyze directory
cua analyze --batch logs/

# Custom configuration
cua analyze --config custom.yaml session.jsonl

# HTML output with interactive charts
cua analyze --format html session.jsonl
```

## Configuration

### Default Configuration
```yaml
# config/default_config.yaml
plan_type: business
hotspot_threshold_std_dev: 2.0
include_charts: true
chart_format: png
include_raw_data: false
report_type: detailed
output_format: markdown
```

### Pricing Configuration
```yaml
# config/pricing/business.yaml
plan_type: business
included_credits_per_month: 1900
credit_to_usd_rate: 0.01
model_pricing:
  openai:
    gpt-4:
      input_per_million: 30
      output_per_million: 60
      cached_read_per_million: 0.1
      cached_write_per_million: 30
  anthropic:
    claude-3-5-sonnet:
      input_per_million: 3
      output_per_million: 15
      cache_write_per_million: 3.75
```

## Testing Strategy

### Test Pyramid
```
        /\
       /E2E\         (5%)
      /------\
     /Integration\   (20%)
    /------------\
   /    Unit       \  (75%)
  /----------------\
```

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Cover edge cases and error conditions
- Target: 80%+ coverage

### Integration Tests
- Test component interactions
- Use sample log files
- Validate end-to-end pipelines
- Target: Key workflows covered

### End-to-End Tests
- Test complete user scenarios
- Use real log files (sanitized)
- Validate output quality
- Target: Critical paths covered

### Test Data
```tests/fixtures/sample_logs/
├── simple_session.jsonl
├── complex_session.jsonl
├── multi_agent_session.jsonl
└── error_session.jsonl
```

## Performance Optimization

### Streaming Processing
- Process JSONL files line by line
- Avoid loading entire file into memory
- Use generators for large datasets

### Lazy Evaluation
- Calculate metrics on demand
- Generate charts only when needed
- Load optional data lazily

### Caching
- Cache parsed session data
- Cache chart images
- Cache pricing calculations

### Parallel Processing
- Process multiple files in parallel
- Generate charts in parallel
- Use multiprocessing for CPU-bound tasks

## Error Handling

### Error Hierarchy
```python
class CopilotAnalyzerError(Exception):
    """Base error for all analyzer errors"""

class ParseError(CopilotAnalyzerError):
    """Error during parsing"""

class ValidationError(CopilotAnalyzerError):
    """Error during validation"""

class ConfigurationError(CopilotAnalyzerError):
    """Error in configuration"""

class ReportGenerationError(CopilotAnalyzerError):
    """Error during report generation"""
```

### Error Handling Strategy
- Fail fast for configuration errors
- Graceful degradation for data errors
- Detailed error messages with context
- Exit codes: 0 (success), 1 (error), 2 (validation)

## Deployment

### Installation Methods

#### PyPI Package
```bash
pip install copilot-usage-analyzer
```

#### From Source
```bash
git clone https://github.com/user/copilot-usage-analyzer
cd copilot-usage-analyzer
pip install -e .
```

#### Docker Image
```bash
docker pull ghcr.io/user/copilot-usage-analyzer:latest
docker run -v $(pwd)/logs:/data copilot-usage-analyzer analyze /data/session.jsonl
```

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -e .[dev]
      - run: pytest --cov
      - run: black --check .
      - run: ruff check .
      - run: mypy src/
```

## Documentation

### Documentation Structure
- **README.md**: Quick start and overview
- **docs/**: Detailed specifications (already created)
- **API.md**: Library API documentation
- **CONTRIBUTING.md**: Contribution guidelines
- **CHANGELOG.md**: Version history

### Code Documentation
- Docstrings for all public APIs
- Type hints throughout
- Inline comments for complex logic
- Sphinx-generated API docs

## Security

### Input Validation
- Validate file paths (prevent directory traversal)
- Validate configuration (prevent code injection)
- Sanitize user input

### Data Privacy
- No data sent to external services
- Option to exclude sensitive data from reports
- Clear documentation of data handling

### Dependency Security
- Regular dependency updates
- Dependabot for vulnerability alerts
- Signed releases

## Monitoring and Logging

### Logging Strategy
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Log Levels
- DEBUG: Detailed diagnostic information
- INFO: General progress information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical failures

### Metrics (Future)
- Parse time
- Report generation time
- Memory usage
- Error rates

## Versioning

### Semantic Versioning
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Process
1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Create git tag
4. Build and publish to PyPI
5. Create GitHub release

## Future Enhancements

### Phase 2
- Web UI for interactive exploration
- Database backend for historical analysis
- Team/organization dashboards
- Integration with GitHub Actions

### Phase 3
- Machine learning for anomaly detection
- Predictive cost forecasting
- Automated optimization suggestions
- Integration with other AI tools

### Phase 4
- Plugin system for custom analyzers
- Real-time monitoring
- Alerting and notifications
- Multi-tenant SaaS offering
