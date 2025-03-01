# dejavu2-cli Tests

This directory contains automated tests for the dejavu2-cli application.

## Test Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests that verify interactions with external services
- `functional/`: End-to-end tests of the CLI functionality
- `fixtures/`: Test data used in tests

## Running Tests

### Prerequisites

- Install test dependencies:
  ```
  pip install pytest pytest-cov
  ```

- Set up API keys (required for integration tests):
  ```
  export OPENAI_API_KEY="your-openai-key"
  export ANTHROPIC_API_KEY="your-anthropic-key"
  ```

### Run All Tests

```bash
cd /path/to/dejavu2-cli
python -m pytest
```

### Run Specific Test Categories

```bash
# Run unit tests only
python -m pytest tests/unit

# Run integration tests only
python -m pytest tests/integration

# Run functional tests only
python -m pytest tests/functional
```

### Run with Coverage Report

```bash
python -m pytest --cov=dejavu2_cli --cov-report=term-missing
```

## Skipping Tests

- Tests requiring API keys will be skipped if the relevant keys are not set in the environment
- Knowledge base tests will be skipped if the okusiassociates.cfg file is not available

## Adding New Tests

When adding new tests:

1. Follow the existing structure and naming conventions
2. Use pytest fixtures where appropriate
3. Mock external services when possible to avoid unnecessary API calls
4. Add appropriate skip conditions for tests requiring external resources