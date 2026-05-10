"""
Functional tests for dejavu2-cli command-line interface.
"""

import os
import subprocess
from pathlib import Path

import pytest

# Path to the CLI executable and Python interpreter
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLI_PATH = os.path.join(PROJECT_ROOT, "dejavu2-cli")
VENV_PYTHON = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")

# Create sample reference text for testing
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_REF = FIXTURES_DIR / "sample.txt"


# Set up sample reference file
@pytest.fixture(scope="module")
def reference_file():
  """Create a temporary reference file for testing."""
  FIXTURES_DIR.mkdir(exist_ok=True)
  with open(SAMPLE_REF, "w") as f:
    f.write("This is a sample reference text.\nIt contains information about Paris, France.")
  yield SAMPLE_REF
  # No cleanup needed as we want to keep the file for future test runs


# Skip if API keys aren't available
require_api_keys = pytest.mark.skipif(
  not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")), reason="No API keys available for testing"
)


class TestDejavu2CLI:
  """Test the dejavu2-cli command line interface."""

  def test_help_option(self):
    """Test that --help displays help information."""
    result = subprocess.run([VENV_PYTHON, CLI_PATH, "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "Options:" in result.stdout

  def test_version(self):
    """Test that --version displays version information."""
    result = subprocess.run([VENV_PYTHON, CLI_PATH, "--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "dejavu2-cli" in result.stdout

  def test_list_models(self):
    """Test that --list-models lists available models."""
    result = subprocess.run([VENV_PYTHON, CLI_PATH, "--list-models"], capture_output=True, text=True)
    assert result.returncode == 0
    # Should at least contain these model types
    assert "claude" in result.stdout.lower() or "gpt" in result.stdout.lower()

  def test_list_templates(self):
    """Test that --list-template-names lists available templates."""
    result = subprocess.run([VENV_PYTHON, CLI_PATH, "--list-template-names"], capture_output=True, text=True)
    assert result.returncode == 0
    # Most likely has a template with "Dejavu" in the name
    assert "Dejavu" in result.stdout or "dejavu" in result.stdout

  def test_status(self):
    """Test that --status displays configuration status."""
    # Need to provide a query when using --status
    result = subprocess.run([VENV_PYTHON, CLI_PATH, "test query", "--status"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "systemprompt" in result.stdout
    # Check for MODEL INFORMATION instead of just model
    assert "MODEL INFORMATION" in result.stdout.upper() or "model" in result.stdout.lower()

  @require_api_keys
  def test_basic_query(self, reference_file):
    """Test a basic query with reference file."""
    result = subprocess.run([VENV_PYTHON, CLI_PATH, "What is the capital of France?", "-r", str(reference_file)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Paris" in result.stdout

  @require_api_keys
  def test_template_query(self):
    """Test query using a template."""
    # Use a known template name instead of trying to parse from output
    result = subprocess.run([VENV_PYTHON, CLI_PATH, "What is the capital of France?", "-T", "Dejavu2 - Helpful AI"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Paris" in result.stdout
