#!/usr/bin/env python3
"""
Custom exception hierarchy for dejavu2-cli.

This module defines a comprehensive exception hierarchy to replace generic
Exception catching and silent failures throughout the codebase. Each exception
type provides specific context for different error conditions.
"""


class DejavuError(Exception):
  """
  Base exception for all dejavu2-cli specific errors.

  All custom exceptions in the application should inherit from this class
  to allow for consistent error handling and logging.
  """

  pass


class ConfigurationError(DejavuError):
  """
  Raised when configuration files cannot be found, loaded, or are invalid.

  Examples:
  - Missing configuration files (defaults.yaml, Models.json, Agents.json)
  - Invalid JSON/YAML syntax in configuration files
  - Missing required configuration keys
  - Invalid configuration values
  """

  pass


class ModelError(DejavuError):
  """
  Raised when model-related operations fail.

  Examples:
  - Requested model not found in Models.json
  - Model is available=0 or enabled=0
  - Invalid model parameters
  - Model definition missing required fields
  """

  pass


class AuthenticationError(DejavuError):
  """
  Raised when API authentication fails.

  Examples:
  - Missing API keys in environment variables
  - Invalid or expired API keys
  - API key format validation failures
  - Quota exceeded errors
  """

  pass


class ConversationError(DejavuError):
  """
  Raised when conversation management operations fail.

  Examples:
  - Conversation file not found
  - Corrupted conversation JSON data
  - Invalid conversation ID format
  - File system permission errors for conversation storage
  """

  pass


class TemplateError(DejavuError):
  """
  Raised when template processing fails.

  Examples:
  - Template file not found
  - Invalid template JSON structure
  - Template key not found during lookup
  - Template parameter validation failures
  """

  pass


class ReferenceError(DejavuError):
  """
  Raised when reference file processing fails.

  Examples:
  - Reference file not found
  - File permission errors
  - File encoding issues
  - Directory traversal security violations
  """

  pass


class KnowledgeBaseError(DejavuError):
  """
  Raised when knowledgebase operations fail.

  Examples:
  - Knowledgebase executable not found
  - Knowledgebase query execution failures
  - Invalid knowledgebase configuration
  - Security validation failures for KB queries
  """

  pass


class APIError(DejavuError):
  """
  Raised when LLM API calls fail.

  Examples:
  - Network connectivity issues
  - API server errors (5xx responses)
  - Rate limiting errors
  - Invalid API responses
  """

  pass


class ValidationError(DejavuError):
  """
  Raised when input validation fails.

  Examples:
  - Invalid parameter values
  - Security validation failures
  - Input format validation errors
  - Constraint violations
  """

  pass


# fin
