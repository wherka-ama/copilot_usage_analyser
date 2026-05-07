# Contributing to Copilot Usage Analyzer

Thank you for your interest in contributing to Copilot Usage Analyzer!

## Setting Up Development Environment

### Prerequisites
- Python 3.9 or higher
- uv (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/wherka-ama/copilot_usage_analyser
cd copilot_usage_analyser
```

2. Install dependencies with uv (recommended, much faster):
```bash
uv sync
```

Or with pip:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Development Workflow

### Running Tests
```bash
pytest
```

### Running Tests with Coverage
```bash
pytest --cov=src/copilot_usage_analyser --cov-report=html
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

### Running All Checks
```bash
black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest
```

## Project Structure

```
copilot_usage_analyser/
├── src/copilot_usage_analyser/
│   ├── cli/              # CLI interface
│   ├── domain/           # Domain layer (entities, services)
│   ├── application/      # Application layer (use cases)
│   └── infrastructure/   # Infrastructure (adapters, charts)
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
├── docs/                 # Documentation
└── config/               # Configuration files
```

## Making Changes

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following the coding standards below

3. Add tests for your changes

4. Run the test suite and ensure all tests pass

5. Commit your changes using conventional commits:
```bash
git commit -m "feat: add new feature"
```

6. Push to your fork and create a pull request

## Coding Standards

### Python Style
- Follow PEP 8
- Use type hints for all public functions
- Write docstrings for all public APIs
- Maximum line length: 100 characters

### Architecture
- Follow hexagonal architecture principles
- Keep domain layer independent of infrastructure
- Use dependency injection
- Write testable code

### Testing
- Write unit tests for all domain logic
- Write integration tests for use cases
- Aim for >80% code coverage
- Use descriptive test names

## Commit Message Convention

We use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```bash
git commit -m "feat: add support for HTML report generation"
git commit -m "fix: correct token calculation for cached tokens"
git commit -m "docs: update README with installation instructions"
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Ensure code follows project standards
5. Write a clear description of your changes

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Sample log file (if applicable, sanitized)

## Questions?

Feel free to open an issue for questions or discussion.
