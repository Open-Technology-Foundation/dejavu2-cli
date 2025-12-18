#!/usr/bin/env python3
"""
Security module for dejavu2-cli.

This module provides secure subprocess execution, input validation, and protection
against command injection attacks. All subprocess calls in the application should
use the secure wrappers provided here.
"""

import logging
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityError(Exception):
  """Base class for security-related errors."""

  pass


class CommandInjectionError(SecurityError):
  """Raised when potential command injection is detected."""

  pass


class ValidationError(SecurityError):
  """Raised when input validation fails."""

  pass


@dataclass
class SubprocessConfig:
  """Configuration for secure subprocess execution."""

  allowed_commands: list[str]
  max_args: int = 10
  timeout: float = 30.0
  allow_shell: bool = False
  working_directory: str | None = None
  environment_whitelist: list[str] | None = None


def validate_knowledgebase_query(query: str) -> str:
  """
  Validate and sanitize knowledgebase query input.

  Args:
      query: Raw query string from user input

  Returns:
      Sanitized query string safe for subprocess execution

  Raises:
      ValidationError: If query contains dangerous patterns
  """
  if not query or not query.strip():
    raise ValidationError("Knowledgebase query cannot be empty")

  # Remove leading/trailing whitespace
  query = query.strip()

  # Length limits
  if len(query) > 1000:
    raise ValidationError("Query too long (max 1000 characters)")

  # Check for dangerous shell metacharacters
  dangerous_patterns = [
    r"[;&|<>`]",  # Basic shell metacharacters (removed ! as it's common punctuation)
    r"\\x[0-9a-fA-F]{2}",  # Hex escape sequences
    r"\\[0-7]{1,3}",  # Octal escape sequences
    r"\$\([^)]*\)",  # Command substitution
    r"`[^`]*`",  # Backtick command substitution
    r"\$\{[^}]*\}",  # Variable expansion
    r"&&",  # AND execution
    r"\|\|",  # OR execution
  ]

  for pattern in dangerous_patterns:
    if re.search(pattern, query):
      raise ValidationError(f"Query contains dangerous pattern: {pattern}")

  # Character whitelist - allow safe characters for natural language queries
  # Allow letters, numbers, spaces, basic punctuation, and common symbols
  # Note: & is excluded as it's a shell metacharacter (background execution)
  safe_pattern = r'^[a-zA-Z0-9\s\-_.,!?:()[\]{}/"\'@#%^*+=~]+$'
  if not re.match(safe_pattern, query):
    raise ValidationError("Query contains invalid characters")

  logger.debug(f"Validated knowledgebase query: {query[:50]}...")
  return query


def validate_editor_path(editor_path: str) -> str:
  """
  Validate editor executable path.

  Args:
      editor_path: Path to editor executable

  Returns:
      Validated absolute path to editor

  Raises:
      ValidationError: If editor path is invalid or dangerous
  """
  if not editor_path or not editor_path.strip():
    raise ValidationError("Editor path cannot be empty")

  editor_path = editor_path.strip()

  # Reject paths with dangerous characters
  dangerous_chars = [";", "&", "|", "<", ">", "`", "$", "(", ")"]
  if any(char in editor_path for char in dangerous_chars):
    raise ValidationError("Editor path contains dangerous characters")

  # Handle editor names vs full paths
  if "/" not in editor_path:
    # Simple editor name - find in PATH
    resolved_path = shutil.which(editor_path)
    if not resolved_path:
      raise ValidationError(f"Editor not found in PATH: {editor_path}")
  else:
    # Full or relative path - resolve it
    try:
      resolved_path = str(Path(editor_path).resolve())
    except (OSError, ValueError) as e:
      raise ValidationError(f"Invalid editor path: {e}")

  # Verify file exists and is executable
  if not Path(resolved_path).exists():
    raise ValidationError(f"Editor not found: {resolved_path}")

  if not Path(resolved_path).is_file():
    raise ValidationError(f"Editor path is not a file: {resolved_path}")

  if not os.access(resolved_path, os.X_OK):
    raise ValidationError(f"Editor is not executable: {resolved_path}")

  logger.debug(f"Validated editor path: {resolved_path}")
  return resolved_path


def validate_file_path(file_path: str, must_exist: bool = False) -> str:
  """
  Validate file path for security issues.

  Args:
      file_path: Path to validate
      must_exist: Whether the file must already exist

  Returns:
      Validated and resolved file path

  Raises:
      ValidationError: If path is invalid or dangerous
  """
  if not file_path or not file_path.strip():
    raise ValidationError("File path cannot be empty")

  file_path = file_path.strip()

  # Check for dangerous patterns
  dangerous_patterns = [
    r"[;&|<>`!]",  # Shell metacharacters
    r"\$\([^)]*\)",  # Command substitution
    r"`[^`]*`",  # Backtick execution
    r"\$\{[^}]*\}",  # Variable expansion
  ]

  for pattern in dangerous_patterns:
    if re.search(pattern, file_path):
      raise ValidationError(f"File path contains dangerous pattern: {pattern}")

  # Resolve path safely
  try:
    resolved_path = str(Path(file_path).resolve())
  except (OSError, ValueError) as e:
    raise ValidationError(f"Invalid file path: {e}")

  # Check existence if required
  if must_exist and not Path(resolved_path).exists():
    raise ValidationError(f"File does not exist: {resolved_path}")

  logger.debug(f"Validated file path: {resolved_path}")
  return resolved_path


class SecureSubprocess:
  """Secure wrapper for subprocess execution."""

  def __init__(self, config: SubprocessConfig):
    self.config = config
    logger.debug(f"Created SecureSubprocess with allowed commands: {config.allowed_commands}")

  def run(self, command: str | list[str], *args, input_data: str | None = None, **kwargs) -> subprocess.CompletedProcess:
    """
    Execute subprocess with security validation.

    Args:
        command: Command to execute (string or list)
        *args: Additional command arguments
        input_data: Data to pass to stdin
        **kwargs: Additional subprocess.run arguments

    Returns:
        CompletedProcess result

    Raises:
        SecurityError: If command fails security validation
    """
    # Convert command to list format
    cmd_list = [command] if isinstance(command, str) else list(command)

    # Add additional arguments
    cmd_list.extend(str(arg) for arg in args)

    # Validate command
    self._validate_command(cmd_list)

    # Set secure defaults
    secure_kwargs = {
      "capture_output": True,
      "text": True,
      "timeout": self.config.timeout,
      "shell": False,  # Never use shell=True
      "check": True,
    }

    # Override with user kwargs (but protect critical security settings)
    protected_keys = {"shell"}
    for key, value in kwargs.items():
      if key not in protected_keys:
        secure_kwargs[key] = value

    # Set secure environment
    if self.config.environment_whitelist:
      secure_env = {}
      for key in self.config.environment_whitelist:
        if key in os.environ:
          secure_env[key] = os.environ[key]
      secure_kwargs["env"] = secure_env

    # Set working directory if specified
    if self.config.working_directory:
      secure_kwargs["cwd"] = self.config.working_directory

    # Add input if provided
    if input_data:
      secure_kwargs["input"] = input_data

    logger.info(f"Executing secure subprocess: {cmd_list[0]} with {len(cmd_list) - 1} args")

    try:
      return subprocess.run(cmd_list, **secure_kwargs)
    except subprocess.TimeoutExpired:
      raise SecurityError(f"Command timed out after {self.config.timeout}s")
    except subprocess.CalledProcessError as e:
      # Re-raise with more context but don't expose sensitive details
      raise SecurityError(f"Command failed with exit code {e.returncode}")
    except Exception as e:
      raise SecurityError(f"Subprocess execution failed: {e}")

  def _validate_command(self, cmd_list: list[str]) -> None:
    """Validate command for security issues."""
    if not cmd_list:
      raise ValidationError("Command cannot be empty")

    if len(cmd_list) > self.config.max_args:
      raise ValidationError(f"Too many arguments (max {self.config.max_args})")

    # Validate executable
    executable = cmd_list[0]
    if not self._is_allowed_command(executable):
      raise ValidationError(f"Command not allowed: {executable}")

    # Validate arguments
    for arg in cmd_list[1:]:
      self._validate_argument(arg)

  def _is_allowed_command(self, command: str) -> bool:
    """Check if command is in whitelist."""
    # Extract just the command name (not full path)
    cmd_name = Path(command).name

    # Also check the full command for exact matches
    return cmd_name in self.config.allowed_commands or command in self.config.allowed_commands

  def _validate_argument(self, arg: str) -> None:
    """Validate individual command argument."""
    # Check for dangerous patterns
    dangerous_patterns = [
      r";\s*\w+",  # Command chaining
      r"\|\s*\w+",  # Piping
      r"&&\s*\w+",  # AND execution
      r"\|\|\s*\w+",  # OR execution
      r"`[^`]*`",  # Backtick execution
      r"\$\([^)]*\)",  # Command substitution
      r"\$\{[^}]*\}",  # Variable expansion
    ]

    for pattern in dangerous_patterns:
      if re.search(pattern, arg):
        raise ValidationError(f"Argument contains dangerous pattern: {pattern}")


# Pre-configured subprocess instances for common use cases
def get_knowledgebase_subprocess() -> SecureSubprocess:
  """Get a secure subprocess configured for knowledgebase operations."""
  config = SubprocessConfig(
    allowed_commands=["customkb"], max_args=6, timeout=300.0, environment_whitelist=["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]
  )
  return SecureSubprocess(config)


def get_editor_subprocess() -> SecureSubprocess:
  """Get a secure subprocess configured for editor operations."""
  config = SubprocessConfig(
    allowed_commands=["nano", "vim", "vi", "emacs", "joe", "mcedit", "micro", "ne", "jed", "gedit"],
    max_args=5,
    timeout=300.0,  # 5 minutes for editing
    environment_whitelist=["TERM", "EDITOR", "DISPLAY"],
  )
  return SecureSubprocess(config)


def escape_for_shell(text: str) -> str:
  """
  Escape text for safe use in shell commands.

  Args:
      text: Text to escape

  Returns:
      Shell-escaped text
  """
  return shlex.quote(text)


# fin
