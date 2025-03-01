#!/bin/bash
# run_tests.sh - Test runner for dejavu2-cli

# Exit immediately if a command exits with a non-zero status, treat unset variables as errors, and pipe failures propagate
set -euo pipefail

# Print help information
function show_help {
  echo "Usage: $0 [OPTION]"
  echo "Run tests for dejavu2-cli"
  echo ""
  echo "Options:"
  echo "  --help, -h       Show this help message and exit"
  echo "  --all, -a        Run all tests (default)"
  echo "  --unit, -u       Run only unit tests"
  echo "  --integration, -i Run only integration tests"
  echo "  --functional, -f Run only functional tests"
  echo "  --coverage, -c   Run tests with coverage report"
  echo "  --verbose, -v    Run tests with verbose output"
  echo ""
  echo "Examples:"
  echo "  $0               Run all tests with normal output"
  echo "  $0 --unit        Run only unit tests"
  echo "  $0 --coverage    Run all tests with coverage report"
}

# Ensure we're in the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
  echo "Activated virtual environment."
else
  echo "Warning: No .venv directory found. Running with system Python."
fi

# Default settings
PYTEST_ARGS=()
TEST_PATH="tests"
VERBOSE=0
COVERAGE=0

# Parse arguments (if any arguments were passed)
if [ $# -gt 0 ]; then
  case "$1" in
    --help|-h)
      show_help
      exit 0
      ;;
    --all|-a)
      TEST_PATH="tests"
      ;;
    --unit|-u)
      TEST_PATH="tests/unit"
      ;;
    --integration|-i)
      TEST_PATH="tests/integration"
      ;;
    --functional|-f)
      TEST_PATH="tests/functional"
      ;;
    --coverage|-c)
      COVERAGE=1
      ;;
    --verbose|-v)
      VERBOSE=1
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
fi

# Add verbosity if requested or by default
if [ $VERBOSE -eq 1 ] || [ $# -eq 0 ]; then
  PYTEST_ARGS+=("-v")
fi

# Handle coverage if requested
if [ $COVERAGE -eq 1 ]; then
  # Check if pytest-cov is installed
  if ! python -c "import pytest_cov" &>/dev/null; then
    echo "Error: pytest-cov is not installed. Run 'pip install pytest-cov' first."
    exit 1
  fi
  PYTEST_ARGS+=("--cov=dejavu2_cli" "--cov-report=term-missing")
  echo "Running tests with coverage report..."
else
  echo "Running tests in $TEST_PATH..."
fi

# Run the tests with all arguments
python -m pytest "${PYTEST_ARGS[@]}" "$TEST_PATH"

# Echo success message
echo "All tests completed successfully."

#fin