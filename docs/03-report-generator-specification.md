# Report Generator Specification for Copilot Usage Analyzer

## Overview
This document specifies the design and behavior of the report generator that creates comprehensive markdown reports with charts and insights from parsed Copilot debug log data.

## Architecture
The report generator follows hexagonal architecture principles:
- **Domain Layer**: Report structure, section generation, insight extraction
- **Application Layer**: Report orchestration and customization
- **Infrastructure Layer**: Chart generation, markdown formatting, file I/O
- **Interface Layer**: CLI and API endpoints

## Report Structure

### Report Sections
1. **Executive Summary**: High-level overview and key findings
2. **Session Overview**: Basic session metadata and timeline
3. **Usage Statistics**: Detailed metrics and statistics
4. **Token Analysis**: Token usage breakdown and cost analysis
5. **Tool Usage**: Tool invocation patterns and efficiency
6. **Temporal Analysis**: Usage patterns over time
7. **Hotspot Analysis**: Anomalous usage patterns and recommendations
8. **Model Performance**: Model-specific analysis
9. **Recommendations**: Actionable insights and optimization suggestions
10. **Appendix**: Detailed event logs and raw data (optional)

### Report Metadata
```python
@dataclass
class ReportMetadata:
    generated_at: str  # ISO 8601 timestamp
    analyzer_version: str
    session_id: str
    log_file_path: str
    plan_type: str
    report_type: str  # summary, detailed, executive
```

## Section Generators

### 1. Executive Summary Generator
**Purpose**: Provide quick overview for stakeholders

**Content**:
- Session title and duration
- Total cost and AI credits used
- Key metrics (turns, tool calls, errors)
- Top 3 findings
- Overall efficiency score (0-100)

**Insight Extraction**:
```python
class ExecutiveSummaryGenerator:
    def generate(self, session: ParsedSession) -> ExecutiveSummary:
        """Generate executive summary"""
        
    def calculate_efficiency_score(self, metrics: SessionMetrics) -> int:
        """Calculate overall efficiency score based on multiple factors"""
        
    def extract_key_findings(self, session: ParsedSession) -> List[str]:
        """Extract top 3 most significant findings"""
```

### 2. Session Overview Generator
**Purpose**: Provide context about the session

**Content**:
- Session timeline (start, end, duration)
- Agent type and model used
- Task description (inferred from events)
- Session summary statistics

**Timeline Visualization**:
- ASCII timeline showing major events
- Time markers for key phases
- Duration breakdown by activity type

### 3. Usage Statistics Generator
**Purpose**: Present core usage metrics

**Content**:
- Total events, model turns, tool calls
- Error count and error rate
- Sub-agent invocations
- Average tokens per turn
- Average duration per turn

**Chart Selection**:
- **Pie Chart**: Event type distribution
- **Bar Chart**: Metric comparison vs baseline

### 4. Token Analysis Generator
**Purpose**: Detailed token usage and cost analysis

**Content**:
- Total tokens by type (input, output, cached)
- Token usage over time
- Cost breakdown by model
- Cache hit rate
- Token efficiency metrics

**Chart Selection**:
- **Stacked Bar Chart**: Token usage over time
- **Pie Chart**: Token type distribution
- **Bar Chart**: Cost by model
- **Line Chart**: Token usage trend

**Cost Calculation**:
- Total cost in USD
- AI credits consumed
- Cost per 1000 tokens
- Comparison to plan limits

### 5. Tool Usage Generator
**Purpose**: Analyze tool invocation patterns

**Content**:
- Tool invocation count and frequency
- Tool success/failure rates
- Average tool duration
- Tools with highest token usage
- Tool efficiency ranking

**Chart Selection**:
- **Horizontal Bar Chart**: Tool invocation counts
- **Scatter Plot**: Tool duration vs token usage
- **Heat Map**: Tool usage over time

### 6. Temporal Analysis Generator
**Purpose**: Analyze usage patterns over time

**Content**:
- Activity timeline with event density
- Peak usage periods
- Idle time analysis
- Session phases (planning, execution, verification)
- Time between turns

**Chart Selection**:
- **Timeline Chart**: Event density over time
- **Line Chart**: Token usage rate over time
- **Area Chart**: Cumulative token usage

### 7. Hotspot Analysis Generator
**Purpose**: Identify and explain anomalous usage

**Content**:
- List of detected hotspots
- Hotspot severity classification
- Context for each hotspot
- Root cause analysis
- Specific recommendations

**Hotspot Categories**:
- High token usage events
- Long duration operations
- Frequent failures
- Excessive turn counts

**Visualization**:
- **Scatter Plot**: Events with hotspots highlighted
- **Table**: Detailed hotspot information

### 8. Model Performance Generator
**Purpose**: Analyze model-specific performance

**Content**:
- Model usage distribution
- Model-specific token efficiency
- Model-specific cost analysis
- Model comparison metrics
- Model switch patterns

**Chart Selection**:
- **Bar Chart**: Model usage comparison
- **Radar Chart**: Model performance across dimensions
- **Stacked Bar**: Model usage over time

### 9. Recommendations Generator
**Purpose**: Provide actionable insights

**Content**:
- Cost optimization recommendations
- Efficiency improvement suggestions
- Error reduction strategies
- Tool usage optimization
- Model selection advice

**Recommendation Categories**:
```python
class RecommendationCategory(Enum):
    COST_OPTIMIZATION = "cost_optimization"
    EFFICIENCY = "efficiency"
    ERROR_REDUCTION = "error_reduction"
    BEST_PRACTICE = "best_practice"
    CONFIGURATION = "configuration"
```

**Recommendation Structure**:
```python
@dataclass
class Recommendation:
    category: RecommendationCategory
    priority: str  # high, medium, low
    title: str
    description: str
    impact_estimate: str
    action_items: List[str]
    related_hotspots: List[str]  # hotspot IDs
```

## Chart Generation

### Chart Library Selection
**Criteria**:
- Minimal dependencies
- Markdown-compatible output
- Support for required chart types
- Easy to maintain

**Recommended**: `matplotlib` with ASCII fallback or `plotly` for interactive charts
- **Primary**: `matplotlib` for static charts (PNG/SVG)
- **Fallback**: ASCII charts for terminal output
- **Alternative**: `plotly` for HTML reports

### Chart Types and Use Cases

| Chart Type | Use Case | Data Required |
|------------|----------|---------------|
| Pie Chart | Proportional distribution | Categorical counts |
| Bar Chart | Comparison | Categorical vs numerical |
| Stacked Bar | Composition over time | Time series with categories |
| Line Chart | Trends | Time series |
| Area Chart | Cumulative values | Time series |
| Scatter Plot | Correlation | Two numerical variables |
| Heat Map | Density/Magnitude | Matrix data |
| Timeline | Sequential events | Event timestamps |
| Radar Chart | Multi-dimensional comparison | Multiple metrics |

### Chart Configuration
```python
@dataclass
class ChartConfig:
    chart_type: ChartType
    title: str
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    width: int = 800
    height: int = 400
    theme: str = "default"
    show_legend: bool = True
    output_format: str = "png"  # png, svg, html, ascii
```

### Chart Generator Interface
```python
class ChartGenerator:
    def generate_chart(self, data: ChartData, config: ChartConfig) -> str:
        """Generate chart and return path or ASCII representation"""
        
    def generate_pie_chart(self, data: Dict[str, int], config: ChartConfig) -> str:
        """Generate pie chart"""
        
    def generate_bar_chart(self, data: Dict[str, int], config: ChartConfig) -> str:
        """Generate bar chart"""
        
    def generate_line_chart(self, data: List[Tuple[str, int]], config: ChartConfig) -> str:
        """Generate line chart"""
```

## Markdown Generation

### Markdown Structure
```markdown
# Copilot Usage Analysis Report

## Executive Summary
[Content]

## Session Overview
[Content with charts]

## Usage Statistics
[Content with charts]

## Token Analysis
[Content with charts]

## Tool Usage
[Content with charts]

## Temporal Analysis
[Content with charts]

## Hotspot Analysis
[Content with charts]

## Model Performance
[Content with charts]

## Recommendations
[Content]

## Appendix
[Optional detailed logs]
```

### Markdown Generator Interface
```python
class MarkdownGenerator:
    def generate_report(self, session: ParsedSession, config: ReportConfig) -> str:
        """Generate complete markdown report"""
        
    def generate_section(self, section_type: SectionType, data: Any) -> str:
        """Generate specific section"""
        
    def embed_chart(self, chart_path: str, caption: str) -> str:
        """Embed chart in markdown"""
        
    def generate_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Generate markdown table"""
```

## Insight Extraction

### Insight Engine
**Purpose**: Automatically derive insights from data

```python
class InsightEngine:
    def extract_insights(self, session: ParsedSession) -> List[Insight]:
        """Extract all insights from session"""
        
    def detect_patterns(self, events: List[Event]) -> List[Pattern]:
        """Detect usage patterns"""
        
    def compare_to_baseline(self, metrics: SessionMetrics, baseline: Baseline) -> Comparison:
        """Compare metrics to baseline"""
```

### Insight Types
1. **Efficiency Insights**: Token efficiency, turn efficiency
2. **Cost Insights**: Cost drivers, optimization opportunities
3. **Error Insights**: Error patterns, failure modes
4. **Pattern Insights**: Usage patterns, workflows
5. **Anomaly Insights**: Unusual behavior, outliers

## Report Configuration

### ReportConfig
```python
@dataclass
class ReportConfig:
    report_type: ReportType = ReportType.DETAILED
    include_charts: bool = True
    chart_format: str = "png"
    include_raw_data: bool = False
    include_appendix: bool = False
    output_format: str = "markdown"  # markdown, html, pdf
    theme: str = "default"
    custom_sections: List[str] = None
```

### ReportType Enum
```python
class ReportType(Enum):
    EXECUTIVE = "executive"  # High-level summary only
    SUMMARY = "summary"  # Key metrics and charts
    DETAILED = "detailed"  # Full analysis
    CUSTOM = "custom"  # User-defined sections
```

## Report Generator Pipeline

### Main Orchestration
```python
class ReportGenerator:
    def __init__(self, section_generators: Dict[SectionType, SectionGenerator],
                 chart_generator: ChartGenerator, markdown_generator: MarkdownGenerator,
                 insight_engine: InsightEngine):
        """Initialize with dependencies"""
        
    def generate_report(self, session: ParsedSession, config: ReportConfig) -> Report:
        """Generate complete report"""
```

### Pipeline Steps
1. **Extract Insights**: Run insight engine on session data
2. **Generate Sections**: Create each section based on report type
3. **Generate Charts**: Create charts for each section
4. **Compose Markdown**: Assemble sections into markdown
5. **Validate**: Ensure report completeness and consistency
6. **Return**: Return complete Report object

## Output Formats

### Markdown (Primary)
- Standard markdown format
- Embedded images for charts
- Tables for tabular data
- Compatible with GitHub, VS Code, etc.

### HTML (Optional)
- Interactive charts using Plotly
- Styled with CSS
- Navigation between sections

### PDF (Optional)
- Generated from HTML/Markdown
- Professional formatting
- Suitable for sharing with stakeholders

## Performance Considerations

### Chart Generation
- Lazy generation (only when needed)
- Caching of chart data
- Parallel chart generation

### Large Sessions
- Sampling for large datasets
- Summary statistics instead of raw data
- Progressive loading

### Memory Management
- Stream markdown generation
- Clean up temporary chart files
- Optional raw data exclusion

## Testing Strategy

### Unit Tests
- Test each section generator independently
- Mock chart generation
- Validate markdown output

### Integration Tests
- Generate complete reports from sample data
- Validate chart generation
- Test different report types

### Visual Regression Tests
- Compare generated charts to expected outputs
- Validate chart styling and formatting

## Extension Points

### Custom Section Generators
```python
class CustomSectionGenerator(SectionGenerator):
    def generate(self, session: ParsedSession) -> Section:
        # Custom section generation logic
```

### Custom Chart Types
```python
class CustomChartGenerator(ChartGenerator):
    def generate_custom_chart(self, data: Any, config: ChartConfig) -> str:
        # Custom chart generation logic
```

### Custom Insight Extractors
```python
class CustomInsightExtractor(InsightEngine):
    def extract_custom_insights(self, session: ParsedSession) -> List[Insight]:
        # Custom insight extraction logic
```

## Report Templates

### Executive Report Template
Focus on:
- Cost summary
- Key metrics
- Top recommendations
- Overall assessment

### Technical Report Template
Focus on:
- Detailed metrics
- Tool usage patterns
- Error analysis
- Performance optimization

### Cost Analysis Report Template
Focus on:
- Cost breakdown
- Token efficiency
- Cost optimization
- Budget tracking
