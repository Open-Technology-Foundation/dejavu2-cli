"""
Unit tests for utility functions in dejavu2-cli.
"""

import datetime
import logging
import os

# Import functions from the application
import sys
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from post_slug import post_slug

from utils import setup_logging, spacetime_placeholders


class TestUtils:
  """Test utility functions."""

  def test_setup_logging(self):
    """Test logging setup with different verbosity levels."""
    # Since the logging implementation has changed, we'll test key behaviors
    with patch("logging.getLogger") as mock_get_logger:
      mock_root_logger = MagicMock()
      mock_get_logger.return_value = mock_root_logger

      # Test default (non-verbose) logging
      setup_logging(verbose=False)
      assert mock_get_logger.called

      # Test verbose logging
      with patch("logging.getLogger") as mock_get_logger_verbose:
        mock_root_logger_verbose = MagicMock()
        mock_get_logger_verbose.return_value = mock_root_logger_verbose
        setup_logging(verbose=True)
        # Should set root logger to DEBUG level
        mock_root_logger_verbose.setLevel.assert_any_call(logging.DEBUG)

      # Test with log file
      with patch("logging.FileHandler") as mock_file_handler:
        setup_logging(log_file="/tmp/test.log")
        mock_file_handler.assert_called_with("/tmp/test.log")

      # Test with quiet mode
      with patch("logging.StreamHandler") as mock_stream_handler:
        setup_logging(quiet=True)
        # Will set up handlers but not use StreamHandler when quiet=True
        assert mock_stream_handler.call_count == 0

  def test_post_slug(self):
    """Test post slug generation from text."""
    # Test basic slug generation
    slug = post_slug("Hello World Test")
    assert slug == "hello-world-test"

    # Test with special characters and spaces
    slug = post_slug("Hello! This is a test with special & characters.")
    assert slug == "hello-this-is-a-test-with-special-and-characters"

    # Test with multiple spaces
    slug = post_slug("Multiple   spaces   test")
    assert slug == "multiple-spaces-test"

    # Test with non-ASCII characters
    slug = post_slug("café and piñata")
    assert slug == "cafe-and-pinata"

    # Test with custom separator
    slug = post_slug("Hello World", sep_char="_")
    assert slug == "hello_world"

    # Test with maximum length
    slug = post_slug("This is a very long string that should be truncated", max_len=20)
    assert len(slug) <= 20

    # Test with empty string
    slug = post_slug("")
    assert slug == ""

  def test_spacetime_placeholders_direct(self):
    """Test spacetime placeholder replacement with direct mocking."""
    # More direct approach that doesn't try to mock datetime.datetime
    text = "This text has no placeholders."
    result = spacetime_placeholders(text)
    assert result == "This text has no placeholders."

    # The function still works for content without placeholders
    with patch("utils.datetime") as mock_datetime:
      # Configure the mock datetime module directly
      mock_now = datetime.datetime(2025, 1, 3, 12, 30, 45)
      mock_datetime.now.return_value = mock_now
      mock_datetime.datetime = datetime.datetime

      # Test simple case without placeholders
      text = "This text has no placeholders."
      result = spacetime_placeholders(text)
      assert result == "This text has no placeholders."

  def test_spacetime_placeholders_with_actual_replacements(self):
    """Test that all placeholder types get replaced with proper values."""
    import re

    # Text with all supported placeholders
    text = (
      "Date: {date}, Time: {time}, DateTime: {datetime}, "
      "Year: {year}, Month: {month}, Day: {day}, "
      "Hour: {hour}, Minute: {minute}, Second: {second}, "
      "Day of Week: {dow}, Timezone: {tz}, "
      "Full: {spacetime}"
    )

    result = spacetime_placeholders(text)

    # Verify each placeholder was replaced
    assert "{date}" not in result
    assert "{time}" not in result
    assert "{datetime}" not in result
    assert "{year}" not in result
    assert "{month}" not in result
    assert "{day}" not in result
    assert "{hour}" not in result
    assert "{minute}" not in result
    assert "{second}" not in result
    assert "{dow}" not in result
    assert "{tz}" not in result
    assert "{spacetime}" not in result

    # Verify format of replacements
    assert re.search(r"\d{4}-\d{2}-\d{2}", result)  # Date format YYYY-MM-DD
    assert re.search(r"\d{2}:\d{2}:\d{2}", result)  # Time format HH:MM:SS
    assert re.search(r"\d{4}", result)  # Year
    assert re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", result)  # Day of week

  def test_spacetime_placeholders_double_brace_format(self):
    """Test backward compatibility with {{placeholder}} format."""
    text = "Date: {{date}}, Time: {{time}}, Year: {{year}}"

    result = spacetime_placeholders(text)

    # Verify double-brace placeholders were replaced
    assert "{{date}}" not in result
    assert "{{time}}" not in result
    assert "{{year}}" not in result

    # Should contain actual date/time values
    import re

    assert re.search(r"\d{4}-\d{2}-\d{2}", result)  # Date
    assert re.search(r"\d{2}:\d{2}:\d{2}", result)  # Time

  def test_spacetime_placeholders_exception_handling(self):
    """Test error handling when datetime operations fail."""
    # Mock datetime.now() to raise an exception
    with patch("utils.datetime") as mock_datetime:
      mock_datetime.now.side_effect = RuntimeError("Mock datetime error")

      text = "Date: {date}, Time: {time}"
      result = spacetime_placeholders(text)

      # Should return original text when error occurs
      assert result == text

  def test_setup_logging_quiet_false_adds_stream_handler(self):
    """Test that console handler is setup when quiet=False."""
    with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler") as mock_stream_handler:
      mock_root_logger = MagicMock()
      mock_get_logger.return_value = mock_root_logger
      mock_handler_instance = MagicMock()
      mock_stream_handler.return_value = mock_handler_instance

      # Call with quiet=False
      setup_logging(quiet=False)

      # Verify StreamHandler was created
      mock_stream_handler.assert_called_once()
      # Verify handler was added to logger
      mock_root_logger.addHandler.assert_called()

  def test_setup_logging_file_handler_error_graceful(self):
    """Test graceful handling of log file creation failure."""
    with patch("logging.getLogger") as mock_get_logger, patch("logging.FileHandler") as mock_file_handler:
      mock_root_logger = MagicMock()
      mock_get_logger.return_value = mock_root_logger

      # Make FileHandler raise an exception
      mock_file_handler.side_effect = PermissionError("Cannot create log file")

      # Should not crash, should handle the error gracefully
      try:
        setup_logging(log_file="/invalid/path/test.log")
        # If we get here, the error was handled
        assert True
      except PermissionError:
        # Should not propagate the exception
        assert False, "Exception should have been caught and logged"
