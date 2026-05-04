# Product/Functional Specification

## Product Overview

### Product Name
Copilot Usage Analyzer (CUA)

### Product Purpose
A command-line tool that analyzes GitHub Copilot Agent Debug Logs to understand usage patterns, identify optimization opportunities, and generate comprehensive reports with actionable insights.

### Target Users
- Development teams using GitHub Copilot
- Engineering managers tracking Copilot adoption and costs
- DevOps engineers monitoring AI tool usage
- Individual developers optimizing their Copilot workflows

### Value Proposition
- **Cost Visibility**: Understand exactly how Copilot credits are being consumed
- **Efficiency Insights**: Identify inefficient usage patterns and optimize workflows
- **Troubleshooting**: Debug complex agent interactions and performance issues
- **Reporting**: Generate professional reports for stakeholders
- **Optimization**: Get actionable recommendations to reduce costs and improve efficiency

## Functional Requirements

### FR-1: Log File Parsing
**Priority**: High

The system shall:
- Accept GitHub Copilot Chat Replay files (`.chatreplay.json`) from VS Code
- Accept GitHub Copilot Agent Debug Log files in OTLP JSON format (future)
- Auto-detect log file format
- Support single file and batch directory processing
- Handle files up to 100MB in size
- Validate file format and structure
- Provide clear error messages for invalid files

**Acceptance Criteria**:
- Given a valid ChatReplay JSON file, the parser successfully extracts all session data
- Given an invalid file format, the system reports a clear error with line number
- Given a directory with multiple log files, the system processes all files
- Format detection correctly identifies ChatReplay vs OTLP format

### FR-2: Session Analysis
**Priority**: High

The system shall:
- Extract session metadata (ID, title, timestamps, duration)
- Calculate aggregate metrics (turns, tool calls, tokens, errors)
- Identify session phases and task progression
- Detect the primary topic/task from event patterns

**Acceptance Criteria**:
- Session duration is calculated accurately from start/end timestamps
- Total token counts match the sum of individual event tokens
- Task description is inferred from initial events with >80% accuracy

### FR-3: Token Usage Analysis
**Priority**: High

The system shall:
- Calculate total input, output, and cached tokens
- Break down token usage by model
- Calculate cache hit rate
- Estimate costs based on plan type and model pricing
- Track token usage over time

**Acceptance Criteria**:
- Token counts are accurate to within 1% of actual values
- Cost estimates match GitHub's pricing calculator
- Cache hit rate is calculated as cached_tokens / total_input_tokens

### FR-4: Tool Usage Analysis
**Priority**: Medium

The system shall:
- Count tool invocations by tool name
- Calculate tool success/failure rates
- Measure average tool duration
- Identify most frequently used tools
- Detect tools with high token consumption

**Acceptance Criteria**:
- Tool invocation counts are accurate
- Success rate is calculated as success_count / total_invocations
- Tools are ranked by invocation count

### FR-5: Temporal Analysis
**Priority**: Medium

The system shall:
- Plot token usage over time
- Identify peak usage periods
- Detect idle time between turns
- Analyze session phases (planning, execution, verification)
- Calculate time between turns

**Acceptance Criteria**:
- Timeline accurately reflects event timestamps
- Peak periods are identified as top 10% of usage density
- Idle time is calculated as gaps > 30 seconds between events

### FR-6: Hotspot Detection
**Priority**: High

The system shall:
- Identify events with anomalously high token usage
- Detect operations with long duration
- Find patterns of frequent failures
- Flag excessive turn counts for single tasks
- Classify hotspot severity (low, medium, high)

**Acceptance Criteria**:
- Hotspots are defined as events > 2 standard deviations from mean
- Severity is based on magnitude of deviation from baseline
- Hotspots are correlated with specific tasks/models

### FR-7: Cost Estimation
**Priority**: High

The system shall:
- Calculate total cost in USD
- Convert to AI credits (1 credit = $0.01)
- Support multiple plan types (business, enterprise, individual)
- Allow custom pricing configuration
- Compare usage to plan limits

**Acceptance Criteria**:
- Cost calculations use correct per-million-token rates
- Default to business plan pricing unless overridden
- Custom pricing can be loaded from configuration file

### FR-8: Report Generation
**Priority**: High

The system shall:
- Generate markdown reports with embedded charts
- Support multiple report types (executive, summary, detailed)
- Include all analysis sections
- Provide actionable recommendations
- Support HTML and PDF output formats (optional)

**Acceptance Criteria**:
- Markdown reports are valid and render correctly
- Charts are embedded as images or ASCII art
- Recommendations are specific and actionable
- Report generation completes within 30 seconds for typical sessions

### FR-9: Insight Extraction
**Priority**: Medium

The system shall:
- Automatically derive insights from usage patterns
- Compare usage to baselines
- Identify optimization opportunities
- Detect inefficient workflows
- Suggest best practices

**Acceptance Criteria**:
- At least 5 insights are generated for typical sessions
- Insights are relevant to the specific session context
- Insights have associated priority levels

### FR-10: CLI Interface
**Priority**: High

The system shall:
- Provide intuitive command-line interface
- Support common use cases with simple commands
- Allow configuration via command-line arguments
- Provide help documentation
- Support configuration files

**Acceptance Criteria**:
- `cua analyze <file>` generates a report
- `cua analyze --help` displays usage information
- Configuration can be provided via `--config` flag
- Error messages are clear and actionable

### FR-11: Configuration
**Priority**: Medium

The system shall:
- Support default configuration (plan: business)
- Allow override via command-line arguments
- Support configuration files (YAML/JSON)
- Validate configuration values
- Provide configuration examples

**Acceptance Criteria**:
- Default configuration works without user input
- Command-line arguments override config file values
- Invalid configuration values are reported with clear errors

### FR-12: Error Handling
**Priority**: High

The system shall:
- Provide clear error messages for all failure modes
- Gracefully handle missing or malformed data
- Continue processing when possible (partial success)
- Log errors with sufficient context
- Exit with appropriate status codes

**Acceptance Criteria**:
- All error paths are tested
- Error messages include file path, line number, and context
- Exit code 0 for success, 1 for errors, 2 for validation failures

## Non-Functional Requirements

### NFR-1: Performance
- Parse a 10MB log file within 10 seconds
- Generate a report within 30 seconds for typical sessions
- Support processing up to 100 sessions in batch mode
- Memory usage < 500MB for typical sessions

### NFR-2: Reliability
- 99% of valid log files parse successfully
- 95% of reports generate without errors
- No data loss during processing
- Graceful degradation for large files

### NFR-3: Usability
- CLI follows standard conventions (GNU style)
- Help text is clear and comprehensive
- Error messages are actionable
- Default behavior meets 80% of use cases

### NFR-4: Maintainability
- Code follows clean architecture principles
- Test coverage > 80%
- Documentation is comprehensive
- Dependencies are minimal and well-maintained

### NFR-5: Extensibility
- New input formats can be added without core changes
- Custom report sections can be added
- New metrics can be calculated
- Pricing models can be updated without code changes

### NFR-6: Portability
- Runs on Linux, macOS, and Windows
- Python 3.9+ compatibility
- No platform-specific dependencies
- Works in CI/CD environments

## User Stories

### US-1: Cost-Conscious Manager
**As a** engineering manager  
**I want** to see how much our team's Copilot usage is costing  
**So that** I can budget accurately and identify cost optimization opportunities

**Acceptance Criteria**:
- Report shows total cost in USD and AI credits
- Cost breakdown by team member/session
- Comparison to plan limits
- Recommendations for cost reduction

### US-2: Developer Optimizing Workflow
**As a** developer  
**I want** to understand which of my Copilot interactions are most expensive  
**So that** I can adjust my workflow to be more efficient

**Acceptance Criteria**:
- Report shows token usage per interaction
- Hotspots identify expensive operations
- Recommendations for reducing token usage
- Tool usage patterns

### US-3: DevOps Troubleshooting
**As a** DevOps engineer  
**I want** to debug why a Copilot agent session took so long  
**So that** I can identify and fix performance issues

**Acceptance Criteria**:
- Timeline shows event sequence and durations
- Long-running operations are highlighted
- Tool call durations are shown
- Error events are identified

### US-4: Team Lead Assessing Adoption
**As a** team lead  
**I want** to see how my team is using Copilot  
**So that** I can assess adoption and identify training needs

**Acceptance Criteria**:
- Aggregate statistics across team sessions
- Tool usage patterns
- Model usage distribution
- Efficiency metrics over time

### US-5: Individual Developer Learning
**As a** developer new to Copilot  
**I want** to see best practices from my own usage  
**So that** I can learn to use Copilot more effectively

**Acceptance Criteria**:
- Recommendations are specific and actionable
- Examples of efficient vs inefficient usage
- Tool usage suggestions
- Model selection advice

## Use Cases

### UC-1: Analyze Single Session
**Actor**: Developer  
**Precondition**: User has exported an Agent Debug Log file  
**Main Flow**:
1. User runs `cua analyze session.jsonl`
2. System parses the log file
3. System calculates metrics and insights
4. System generates markdown report
5. System saves report to `session-report.md`
6. System displays success message with report path

**Postcondition**: Report file is generated and contains analysis

### UC-2: Batch Analyze Directory
**Actor**: Engineering Manager  
**Precondition**: User has directory with multiple log files  
**Main Flow**:
1. User runs `cua analyze --batch logs/`
2. System processes all log files in directory
3. System generates individual reports for each file
4. System generates aggregate summary report
5. System displays summary statistics

**Postcondition**: All reports generated with aggregate summary

### UC-3: Custom Plan Configuration
**Actor**: DevOps Engineer  
**Precondition**: User has custom pricing configuration  
**Main Flow**:
1. User creates pricing config file
2. User runs `cua analyze --config pricing.yaml session.jsonl`
3. System loads custom pricing
4. System calculates costs using custom rates
5. System generates report with custom cost calculations

**Postcondition**: Report uses custom pricing configuration

### UC-4: Generate Executive Report
**Actor**: Engineering Manager  
**Precondition**: User needs high-level summary for stakeholders  
**Main Flow**:
1. User runs `cua analyze --type executive session.jsonl`
2. System generates executive summary only
3. Report focuses on cost and key metrics
4. Report includes top recommendations

**Postcondition**: Concise executive report is generated

### UC-5: Export to HTML
**Actor**: Developer  
**Precondition**: User wants interactive report  
**Main Flow**:
1. User runs `cua analyze --format html session.jsonl`
2. System generates HTML report
3. Charts are interactive (Plotly)
4. Report includes navigation

**Postcondition**: Interactive HTML report is generated

## Data Requirements

### Input Data
- **Format**: OTLP JSON/JSONL
- **Size**: Up to 100MB per file
- **Encoding**: UTF-8
- **Required Fields**: Session metadata, event timestamps, token counts

### Output Data
- **Format**: Markdown (primary), HTML (optional), PDF (optional)
- **Charts**: PNG/SVG images or ASCII art
- **Size**: Typically 1-5MB per report
- **Encoding**: UTF-8

### Configuration Data
- **Format**: YAML or JSON
- **Location**: `~/.cua/config.yaml` or `--config` flag
- **Required Fields**: None (defaults provided)

## Security Considerations

### Data Privacy
- Log files may contain sensitive code snippets
- Reports should not expose sensitive data
- Option to exclude raw data from reports

### File Access
- Read-only access to input files
- Write access to output directory
- No network access required

### Configuration Security
- Configuration files should be validated
- No execution of arbitrary code from config

## Compliance

### GitHub Terms of Service
- Tool respects GitHub's data usage policies
- No reverse engineering of Copilot internals
- Use of debug logs is within intended purpose

### Open Source Licensing
- Tool will be open source
- Compatible with common licenses (MIT, Apache 2.0)
- No proprietary dependencies

## Success Metrics

### Adoption
- 100+ GitHub stars within 6 months
- 50+ active users within 3 months
- Positive feedback from community

### Quality
- < 5% reported bugs
- 80%+ test coverage
- Documentation completeness score > 90%

### Performance
- 95% of analyses complete within 30 seconds
- 99% of valid files parse successfully
- Memory usage within specified limits

## Roadmap

### Phase 1: MVP (Current)
- Core parsing functionality
- Basic metrics calculation
- Markdown report generation
- CLI interface

### Phase 2: Enhanced Analysis
- Advanced hotspot detection
- Insight engine
- Custom report templates
- HTML output

### Phase 3: Advanced Features
- Batch processing with aggregation
- Historical trend analysis
- Team/organization dashboards
- Integration with CI/CD

### Phase 4: Ecosystem
- VS Code extension
- Web UI
- API for integration
- Plugin system
