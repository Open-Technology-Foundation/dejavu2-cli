#!/usr/bin/env python3
"""
Utility functions for dejavu2-cli.

This module contains helper functions for:
- Logging setup
- String processing
- Date/time utilities
"""

import logging
import warnings
from datetime import datetime

import tzlocal


# Setup logging
def setup_logging(verbose=False, log_file=None, quiet=True):
  """
  Configure logging for the application with proper formatting and filters.

  Args:
      verbose: Whether to use DEBUG level logging (default: False)
      log_file: Path to a log file to write logs to (default: None)
      quiet: Whether to suppress console output (default: True)

  Returns:
      The configured root logger instance
  """
  # Configure root logger
  root_logger = logging.getLogger()

  # Clear any existing handlers to avoid duplicate logs
  for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

  # Set log level based on verbosity
  root_level = logging.DEBUG if verbose else logging.INFO

  root_logger.setLevel(root_level)

  # Create formatters
  detailed_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

  console_formatter = logging.Formatter("%(levelname)s - %(name)s: %(message)s")

  # Set up console handler unless quiet mode is enabled
  if not quiet:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(root_level)
    root_logger.addHandler(console_handler)

  # Set up file handler if a log file is specified
  if log_file:
    try:
      file_handler = logging.FileHandler(log_file)
      file_handler.setFormatter(detailed_formatter)
      file_handler.setLevel(logging.DEBUG)  # Always log everything to file
      root_logger.addHandler(file_handler)
    except Exception as e:
      logging.error(f"Failed to set up log file: {str(e)}")

  # Get the utils logger (this module)
  logger = logging.getLogger(__name__)

  # Configure third-party library loggers
  # Suppress warnings from specific modules
  warnings.filterwarnings("ignore", category=UserWarning, module=r"^anthropic\..*")
  warnings.filterwarnings("ignore", category=UserWarning, module=r"^openai\..*")

  # Set conservative logging levels for noisy libraries
  logging.getLogger("anthropic").setLevel(logging.WARNING)
  logging.getLogger("openai").setLevel(logging.WARNING)
  logging.getLogger("httpx").setLevel(logging.WARNING)
  logging.getLogger("urllib3").setLevel(logging.WARNING)

  # Log the logging configuration
  logger.debug(f"Logging initialized (verbose={verbose}, log_file={log_file}, quiet={quiet})")

  return root_logger


def spacetime_placeholders(text: str) -> str:
  """
  Replace date/time placeholders in a text string with current values.

  Supported placeholders:
  - {date}: Current date in YYYY-MM-DD format
  - {time}: Current time in HH:MM:SS format
  - {datetime}: Combined date and time (YYYY-MM-DD HH:MM:SS)
  - {year}: Current year (YYYY)
  - {month}: Current month (MM)
  - {day}: Current day (DD)
  - {hour}: Current hour (HH)
  - {minute}: Current minute (MM)
  - {second}: Current second (SS)
  - {dow}: Current day of week name (e.g., "Monday")
  - {tz}: Current timezone name
  - {spacetime}: Complete string with day, date, time, and timezone

  Args:
      text: The string containing placeholders to replace

  Returns:
      String with placeholders replaced by current values

  Example:
      >>> spacetime_placeholders("Today is {date} at {time}")
      'Today is 2025-01-03 at 12:30:45'
  """
  if not text or not isinstance(text, str):
    return text

  if "{" not in text:
    return text

  try:
    now = datetime.now()

    # Create map of placeholders to their values
    replacements = {
      "{date}": now.strftime("%Y-%m-%d"),
      "{time}": now.strftime("%H:%M:%S"),
      "{datetime}": now.strftime("%Y-%m-%d %H:%M:%S"),
      "{year}": now.strftime("%Y"),
      "{month}": now.strftime("%m"),
      "{day}": now.strftime("%d"),
      "{hour}": now.strftime("%H"),
      "{minute}": now.strftime("%M"),
      "{second}": now.strftime("%S"),
      "{dow}": now.strftime("%A"),  # Full day name
      "{tz}": str(tzlocal.get_localzone().key),
    }

    # Add spacetime after we have all the other values
    replacements["{spacetime}"] = f"{replacements['{dow}']} {replacements['{date}']} {replacements['{time}']} {replacements['{tz}']}"

    # Replace each placeholder in the text
    result = text
    for placeholder, value in replacements.items():
      result = result.replace(placeholder, value)

      # Also handle double-brace format for backward compatibility
      double_brace = placeholder.replace("{", "{{").replace("}", "}}")
      result = result.replace(double_brace, value)

    return result
  except Exception as e:
    # Log but don't crash on date/time errors
    logging.warning(f"Error processing date/time placeholders: {str(e)}")
    return text
