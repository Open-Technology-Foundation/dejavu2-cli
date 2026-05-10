"""
Tests for knowledgebase integration in dejavu2-cli.
"""

import os

# Import the knowledgebase function from context.py
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from context import get_knowledgebase_string

# Skip if knowledgebase path is not configured or customkb not installed
kb_available = pytest.mark.skipif(
  not os.path.exists(os.path.join(os.environ.get("VECTORDBS", "/var/lib/vectordbs"), "okusi/okusiassociates.cfg")),
  reason="okusiassociates.cfg knowledgebase not available",
)


class TestKnowledgeBase:
  """Test interactions with knowledgebases."""

  @kb_available
  def test_kb_query(self):
    """Test querying the okusiassociates knowledgebase."""
    result = get_knowledgebase_string(knowledgebase="okusiassociates", knowledgebase_query="What services does the company offer?")

    # Check that we got a proper response
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
    assert "<knowledgebase>" in result
    assert "</knowledgebase>" in result

  @patch("context.validate_knowledgebase_query")
  @patch("context.validate_file_path")
  @patch("context.os.path.exists")
  @patch("context.get_knowledgebase_subprocess")
  def test_kb_query_mocked(self, mock_get_subprocess, mock_exists, mock_validate_path, mock_validate_query):
    """Test knowledgebase query with a mocked subprocess call."""
    # Set up validation mocks
    mock_validate_query.return_value = "What services does the company offer?"
    mock_validate_path.side_effect = lambda x, must_exist=False: x  # Return path as-is
    mock_exists.return_value = True  # Pretend files exist

    # Set up subprocess mock
    mock_subprocess = MagicMock()
    mock_process = MagicMock()
    mock_process.stdout = "Okusi Associates offers software development and consulting services."
    mock_process.returncode = 0
    mock_subprocess.run.return_value = mock_process
    mock_get_subprocess.return_value = mock_subprocess

    # Call the function
    result = get_knowledgebase_string(
      knowledgebase="okusiassociates",
      knowledgebase_query="What services does the company offer?",
      customkb_executable="/usr/local/bin/customkb",
      vectordbs_path="/var/lib/vectordbs",
      api_keys={"ANTHROPIC_API_KEY": "test-key"},
    )

    # Verify the result
    assert "<knowledgebase>" in result
    assert "Okusi Associates offers software development" in result
    assert "</knowledgebase>" in result

    # Verify subprocess was called
    mock_subprocess.run.assert_called_once()
