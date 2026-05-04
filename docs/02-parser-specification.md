# Parser Specification for Copilot Debug Logs

## Overview
This document specifies the design and behavior of the parser that extracts and transforms GitHub Copilot Agent Debug Logs into the standardized schema defined in the JSON Schema Design document.

## Architecture
The parser follows hexagonal architecture principles with clear separation of concerns:
- **Domain Layer**: Core parsing logic and data models
- **Application Layer**: Orchestration and use cases
- **Infrastructure Layer**: File I/O and format-specific adapters
- **Interface Layer**: CLI and API endpoints

## Input Formats

### Primary Format: VS Code Chat Replay (`.chatreplay.json`)
The parser supports VS Code Chat Replay format exported from VS Code.
- File extension: `.json`
- Format: Single JSON object with nested structure
- Structure: `exportedAt`, `totalPrompts`, `totalLogEntries`, `prompts` array

### Secondary Format: OTLP JSON (JSONL)
The parser supports OpenTelemetry JSON format exported from VS Code Agent Debug Log panel (future).
- File extension: `.jsonl` or `.json`
- Format: JSON Lines (one JSON object per line) or single JSON array
- Structure: `resourceSpans` array with span data

### Supported Variations
1. **Single ChatReplay file**: Complete VS Code chat replay export
2. **Single OTLP file**: Complete OTLP export with all spans
3. **JSONL file**: Line-delimited JSON with one span per line (OTLP)
4. **Multiple files**: Batch processing of multiple session files

## Parser Components

### 1. File Reader (Infrastructure Layer)
**Responsibility**: Read log files from disk with appropriate error handling

**Interface**:
```python
class LogFileReader:
    def read_file(self, file_path: str) -> Dict:
        """Read log file and return JSON data"""
        
    def detect_format(self, file_path: str) -> str:
        """Detect log file format (chatreplay or otlp)"""
        
    def read_directory(self, directory_path: str) -> Iterator[Tuple[str, Dict]]:
        """Read all log files in directory"""
```

**Error Handling**:
- File not found: Raise `FileNotFoundError` with clear message
- Invalid JSON: Raise `ParseError` with line number and context
- Permission denied: Raise `PermissionError`

### 2. ChatReplay Adapter (Infrastructure Layer)
**Responsibility**: Transform VS Code ChatReplay format to internal domain model

**Interface**:
```python
class ChatReplayAdapter:
    def adapt(self, chatreplay_data: Dict) -> Tuple[Session, List[Event]]:
        """Transform ChatReplay data to internal session and events"""
        
    def extract_session_info(self, data: Dict) -> Session:
        """Extract session metadata from ChatReplay root"""
        
    def extract_events_from_prompt(self, prompt_data: Dict) -> List[Event]:
        """Extract events from a single prompt"""
```

**Mapping Rules**:
- ChatReplay `exportedAt` → Session metadata
- ChatReplay `prompts` → Event groups
- ChatReplay `logs` with `kind=toolCall` → Tool call events
- ChatReplay `logs` with `kind=request` → Model turn events
- ChatReplay `metadata.usage` → Token usage
- ChatReplay `metadata.model` → Model information

### 3. OTLP Adapter (Infrastructure Layer)
**Responsibility**: Transform OTLP format to internal domain model

**Interface**:
```python
class OTLPAdapter:
    def adapt(self, otlp_data: List[Dict]) -> Tuple[Session, List[Event]]:
        """Transform OTLP data to internal session and events"""
        
    def extract_session_info(self, resource: Dict) -> Session:
        """Extract session metadata from resource attributes"""
        
    def extract_events(self, spans: List[Dict]) -> List[Event]:
        """Transform spans to event objects"""
```

**Mapping Rules**:
- OTLP `resource.attributes` → Session metadata
- OTLP `spans` → Events
- OTLP `span.attributes` → Event details
- OTLP `span.events` → Sub-events (tool calls, etc.)

### 3. Event Parser (Domain Layer)
**Responsibility**: Parse individual events and extract structured data

**Interface**:
```python
class EventParser:
    def parse(self, raw_event: Dict) -> Event:
        """Parse raw event data into structured Event object"""
        
    def extract_token_usage(self, attributes: Dict) -> TokenUsage:
        """Extract token counts from event attributes"""
        
    def extract_tool_info(self, attributes: Dict) -> ToolInfo:
        """Extract tool call information"""
        
    def extract_error_info(self, attributes: Dict) -> ErrorInfo:
        """Extract error information"""
```

**Event Type Detection**:
Based on OTLP span names and attributes:
- `model_turn` / `llm_request`: Model turn event
- `tool_call` / `tool_invocation`: Tool call event
- `discovery` / `file_discovery`: Discovery event
- `error` / `exception`: Error event
- `sub_agent` / `agent_handoff`: Sub-agent event

### 4. Metrics Calculator (Domain Layer)
**Responsibility**: Calculate aggregate statistics from events

**Interface**:
```python
class MetricsCalculator:
    def calculate_session_metrics(self, session: InternalSession) -> SessionMetrics:
        """Calculate aggregate metrics for session"""
        
    def calculate_token_usage_by_model(self, events: List[Event]) -> List[ModelTokenUsage]:
        """Group token usage by model"""
        
    def calculate_tool_usage(self, events: List[Event]) -> List[ToolUsageStats]:
        """Calculate tool usage statistics"""
        
    def calculate_hotspots(self, events: List[Event]) -> List[Hotspot]:
        """Identify usage hotspots"""
```

**Hotspot Detection Algorithm**:
1. Calculate baseline statistics (mean, std dev) for key metrics
2. Identify events exceeding threshold (e.g., > 2 std dev)
3. Classify hotspot type based on metric exceeded
4. Assign severity based on magnitude of deviation

### 5. Cost Calculator (Domain Layer)
**Responsibility**: Calculate estimated costs based on token usage and pricing

**Interface**:
```python
class CostCalculator:
    def __init__(self, pricing_config: PricingConfig):
        """Initialize with pricing configuration"""
        
    def calculate_session_cost(self, token_usage: TokenUsage, model: str) -> Cost:
        """Calculate cost for session"""
        
    def calculate_total_cost(self, session: InternalSession) -> TotalCost:
        """Calculate total cost across all models"""
```

**Pricing Configuration**:
- Default: Business plan pricing
- Overrideable via CLI argument or config file
- Supports multiple plan types (business, enterprise, individual)

## Parser Pipeline

### Main Parser Orchestration (Application Layer)
```python
class AnalyzeSession:
    def __init__(self, reader: LogFileReader, chatreplay_adapter: ChatReplayAdapter,
                 otlp_adapter: OTLPAdapter, metrics_calculator: MetricsCalculator,
                 cost_calculator: CostCalculator, hotspot_detector: HotspotDetector):
        """Initialize parser with dependencies"""
        
    def execute(self, file_path: str) -> ParsedSession:
        """Parse and analyze single log file"""
```

### Pipeline Steps
1. **Read File**: Load raw JSON data
2. **Detect Format**: Determine if ChatReplay or OTLP format
3. **Adapt Format**: Transform to internal model using appropriate adapter
4. **Parse Events**: Extract structured data from each event
5. **Calculate Metrics**: Compute aggregate statistics
6. **Calculate Costs**: Estimate costs based on usage
7. **Detect Hotspots**: Identify anomalous usage patterns
8. **Validate**: Ensure data consistency and completeness
9. **Return**: Return standardized ParsedSession object

## Error Handling Strategy

### Validation Rules
1. **Session Validation**:
   - Must have session_id
   - Must have valid timestamps
   - End time must be after start time
   - Duration must be positive

2. **Event Validation**:
   - Must have event_id
   - Must have valid timestamp
   - Timestamp must be within session bounds
   - Event type must be recognized

3. **Token Validation**:
   - Token counts must be non-negative
   - Input + cached >= output (sanity check)
   - Total tokens must be consistent

### Error Types
```python
class ParseError(Exception):
    """Base parse error"""
    
class InvalidFormatError(ParseError):
    """Invalid file format"""
    
class ValidationError(ParseError):
    """Data validation failed"""
    
class MissingFieldError(ParseError):
    """Required field missing"""
```

### Recovery Strategies
- **Soft Errors**: Log warning, continue processing
- **Hard Errors**: Stop processing, report error
- **Partial Success**: Return partial results with error summary

## Configuration

### ParserConfig
```python
@dataclass
class ParserConfig:
    plan_type: str = "business"  # business, enterprise, individual
    custom_pricing_file: Optional[str] = None
    hotspot_threshold_std_dev: float = 2.0
    include_raw_data: bool = False
    validate_strict: bool = True
```

### PricingConfig
```python
@dataclass
class PricingConfig:
    plan_type: str
    included_credits_per_month: int
    credit_to_usd_rate: float
    model_pricing: Dict[str, ModelPricing]
```

## Performance Considerations

### Memory Management
- Stream processing for large files (JSONL)
- Lazy loading of event details
- Optional raw data inclusion

### Processing Speed
- Parallel processing for multiple files
- Incremental metric calculation
- Caching of expensive operations

### Scalability
- Support for sessions with 10,000+ events
- Handle files up to 100MB
- Process multiple sessions concurrently

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock dependencies
- Cover edge cases and error conditions

### Integration Tests
- Test parser pipeline end-to-end
- Use sample log files (synthetic)
- Validate output against expected schema

### Property-Based Tests
- Generate random valid inputs
- Verify invariants (e.g., total tokens = sum of event tokens)
- Test with malformed inputs

## Output Format

The parser outputs a `ParsedSession` object that matches the JSON schema defined in `01-json-schema-design.md`. This can be serialized to JSON for further processing or directly used by the report generator.

## Extension Points

### Custom Adapters
New input formats can be supported by implementing the `OTLPAdapter` interface:
```python
class CustomAdapter(OTLPAdapter):
    def adapt(self, data: Dict) -> InternalSession:
        # Custom transformation logic
```

### Custom Event Parsers
Specialized event types can be handled by extending `EventParser`:
```python
class CustomEventParser(EventParser):
    def parse(self, raw_event: Dict) -> Event:
        # Custom parsing logic
```

### Custom Metric Calculators
Additional metrics can be calculated by extending `MetricsCalculator`:
```python
class CustomMetricsCalculator(MetricsCalculator):
    def calculate_custom_metric(self, events: List[Event]) -> CustomMetric:
        # Custom metric calculation
```
