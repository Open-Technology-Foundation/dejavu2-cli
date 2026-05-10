#!/usr/bin/env python3
"""
Unit tests for custom exception hierarchy in dejavu2-cli.

This module tests all custom exception classes to ensure proper inheritance,
instantiation, message handling, and exception catching behavior.
"""

import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from errors import (
  APIError,
  AuthenticationError,
  ConfigurationError,
  ConversationError,
  DejavuError,
  KnowledgeBaseError,
  ModelError,
  ReferenceError,
  TemplateError,
  ValidationError,
)


class TestDejavuErrorBase:
  """Test the base DejavuError exception class."""

  def test_dejavu_error_can_be_raised(self):
    """Test that DejavuError can be raised and caught."""
    with pytest.raises(DejavuError):
      raise DejavuError("Test error")

  def test_dejavu_error_inherits_from_exception(self):
    """Test that DejavuError inherits from Exception."""
    assert issubclass(DejavuError, Exception)

  def test_dejavu_error_carries_message(self):
    """Test that DejavuError can carry a custom message."""
    message = "Custom error message"
    error = DejavuError(message)
    assert str(error) == message

  def test_dejavu_error_can_be_caught_as_exception(self):
    """Test that DejavuError can be caught as generic Exception."""
    with pytest.raises(Exception):
      raise DejavuError("Test error")


class TestConfigurationError:
  """Test the ConfigurationError exception class."""

  def test_configuration_error_can_be_raised(self):
    """Test that ConfigurationError can be raised."""
    with pytest.raises(ConfigurationError):
      raise ConfigurationError("Configuration file not found")

  def test_configuration_error_inherits_from_dejavu_error(self):
    """Test that ConfigurationError inherits from DejavuError."""
    assert issubclass(ConfigurationError, DejavuError)

  def test_configuration_error_can_be_caught_as_dejavu_error(self):
    """Test that ConfigurationError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise ConfigurationError("Test error")

  def test_configuration_error_carries_message(self):
    """Test that ConfigurationError carries error message."""
    message = "defaults.yaml not found"
    error = ConfigurationError(message)
    assert str(error) == message


class TestModelError:
  """Test the ModelError exception class."""

  def test_model_error_can_be_raised(self):
    """Test that ModelError can be raised."""
    with pytest.raises(ModelError):
      raise ModelError("Model not found")

  def test_model_error_inherits_from_dejavu_error(self):
    """Test that ModelError inherits from DejavuError."""
    assert issubclass(ModelError, DejavuError)

  def test_model_error_can_be_caught_as_dejavu_error(self):
    """Test that ModelError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise ModelError("Test error")

  def test_model_error_carries_message(self):
    """Test that ModelError carries error message."""
    message = "Model 'gpt-999' not found"
    error = ModelError(message)
    assert str(error) == message


class TestAuthenticationError:
  """Test the AuthenticationError exception class."""

  def test_authentication_error_can_be_raised(self):
    """Test that AuthenticationError can be raised."""
    with pytest.raises(AuthenticationError):
      raise AuthenticationError("API key missing")

  def test_authentication_error_inherits_from_dejavu_error(self):
    """Test that AuthenticationError inherits from DejavuError."""
    assert issubclass(AuthenticationError, DejavuError)

  def test_authentication_error_can_be_caught_as_dejavu_error(self):
    """Test that AuthenticationError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise AuthenticationError("Test error")

  def test_authentication_error_carries_message(self):
    """Test that AuthenticationError carries error message."""
    message = "OPENAI_API_KEY not found in environment"
    error = AuthenticationError(message)
    assert str(error) == message


class TestConversationError:
  """Test the ConversationError exception class."""

  def test_conversation_error_can_be_raised(self):
    """Test that ConversationError can be raised."""
    with pytest.raises(ConversationError):
      raise ConversationError("Conversation file corrupted")

  def test_conversation_error_inherits_from_dejavu_error(self):
    """Test that ConversationError inherits from DejavuError."""
    assert issubclass(ConversationError, DejavuError)

  def test_conversation_error_can_be_caught_as_dejavu_error(self):
    """Test that ConversationError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise ConversationError("Test error")

  def test_conversation_error_carries_message(self):
    """Test that ConversationError carries error message."""
    message = "Conversation ID abc123 not found"
    error = ConversationError(message)
    assert str(error) == message


class TestTemplateError:
  """Test the TemplateError exception class."""

  def test_template_error_can_be_raised(self):
    """Test that TemplateError can be raised."""
    with pytest.raises(TemplateError):
      raise TemplateError("Template not found")

  def test_template_error_inherits_from_dejavu_error(self):
    """Test that TemplateError inherits from DejavuError."""
    assert issubclass(TemplateError, DejavuError)

  def test_template_error_can_be_caught_as_dejavu_error(self):
    """Test that TemplateError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise TemplateError("Test error")

  def test_template_error_carries_message(self):
    """Test that TemplateError carries error message."""
    message = "Template 'MyTemplate' not found in Agents.json"
    error = TemplateError(message)
    assert str(error) == message


class TestReferenceError:
  """Test the ReferenceError exception class."""

  def test_reference_error_can_be_raised(self):
    """Test that ReferenceError can be raised."""
    with pytest.raises(ReferenceError):
      raise ReferenceError("Reference file not found")

  def test_reference_error_inherits_from_dejavu_error(self):
    """Test that ReferenceError inherits from DejavuError."""
    assert issubclass(ReferenceError, DejavuError)

  def test_reference_error_can_be_caught_as_dejavu_error(self):
    """Test that ReferenceError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise ReferenceError("Test error")

  def test_reference_error_carries_message(self):
    """Test that ReferenceError carries error message."""
    message = "Reference file '/path/to/file.txt' not found"
    error = ReferenceError(message)
    assert str(error) == message


class TestKnowledgeBaseError:
  """Test the KnowledgeBaseError exception class."""

  def test_knowledgebase_error_can_be_raised(self):
    """Test that KnowledgeBaseError can be raised."""
    with pytest.raises(KnowledgeBaseError):
      raise KnowledgeBaseError("Knowledgebase query failed")

  def test_knowledgebase_error_inherits_from_dejavu_error(self):
    """Test that KnowledgeBaseError inherits from DejavuError."""
    assert issubclass(KnowledgeBaseError, DejavuError)

  def test_knowledgebase_error_can_be_caught_as_dejavu_error(self):
    """Test that KnowledgeBaseError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise KnowledgeBaseError("Test error")

  def test_knowledgebase_error_carries_message(self):
    """Test that KnowledgeBaseError carries error message."""
    message = "Knowledgebase 'okusi' not found"
    error = KnowledgeBaseError(message)
    assert str(error) == message


class TestAPIError:
  """Test the APIError exception class."""

  def test_api_error_can_be_raised(self):
    """Test that APIError can be raised."""
    with pytest.raises(APIError):
      raise APIError("API request failed")

  def test_api_error_inherits_from_dejavu_error(self):
    """Test that APIError inherits from DejavuError."""
    assert issubclass(APIError, DejavuError)

  def test_api_error_can_be_caught_as_dejavu_error(self):
    """Test that APIError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise APIError("Test error")

  def test_api_error_carries_message(self):
    """Test that APIError carries error message."""
    message = "OpenAI API returned 500 error"
    error = APIError(message)
    assert str(error) == message


class TestValidationError:
  """Test the ValidationError exception class."""

  def test_validation_error_can_be_raised(self):
    """Test that ValidationError can be raised."""
    with pytest.raises(ValidationError):
      raise ValidationError("Invalid parameter")

  def test_validation_error_inherits_from_dejavu_error(self):
    """Test that ValidationError inherits from DejavuError."""
    assert issubclass(ValidationError, DejavuError)

  def test_validation_error_can_be_caught_as_dejavu_error(self):
    """Test that ValidationError can be caught as DejavuError."""
    with pytest.raises(DejavuError):
      raise ValidationError("Test error")

  def test_validation_error_carries_message(self):
    """Test that ValidationError carries error message."""
    message = "Temperature must be between 0 and 2"
    error = ValidationError(message)
    assert str(error) == message


class TestExceptionHierarchy:
  """Test the overall exception hierarchy and relationships."""

  def test_all_custom_exceptions_inherit_from_dejavu_error(self):
    """Test that all custom exceptions inherit from DejavuError."""
    exception_classes = [
      ConfigurationError,
      ModelError,
      AuthenticationError,
      ConversationError,
      TemplateError,
      ReferenceError,
      KnowledgeBaseError,
      APIError,
      ValidationError,
    ]

    for exc_class in exception_classes:
      assert issubclass(exc_class, DejavuError), f"{exc_class.__name__} should inherit from DejavuError"

  def test_all_custom_exceptions_inherit_from_exception(self):
    """Test that all custom exceptions inherit from Exception."""
    exception_classes = [
      DejavuError,
      ConfigurationError,
      ModelError,
      AuthenticationError,
      ConversationError,
      TemplateError,
      ReferenceError,
      KnowledgeBaseError,
      APIError,
      ValidationError,
    ]

    for exc_class in exception_classes:
      assert issubclass(exc_class, Exception), f"{exc_class.__name__} should inherit from Exception"

  def test_exception_types_are_distinct(self):
    """Test that different exception types are not the same class."""
    # ConfigurationError is not ModelError
    assert ConfigurationError is not ModelError
    # AuthenticationError is not APIError
    assert AuthenticationError is not APIError
    # All are distinct types
    exception_classes = [
      DejavuError,
      ConfigurationError,
      ModelError,
      AuthenticationError,
      ConversationError,
      TemplateError,
      ReferenceError,
      KnowledgeBaseError,
      APIError,
      ValidationError,
    ]

    # Check that all classes are distinct
    for i, exc1 in enumerate(exception_classes):
      for exc2 in exception_classes[i + 1 :]:
        assert exc1 is not exc2, f"{exc1.__name__} and {exc2.__name__} should be distinct"

  def test_can_catch_multiple_exceptions_as_dejavu_error(self):
    """Test that multiple exception types can all be caught as DejavuError."""
    exceptions_to_test = [
      ConfigurationError("config"),
      ModelError("model"),
      AuthenticationError("auth"),
      ConversationError("conversation"),
      TemplateError("template"),
      ReferenceError("reference"),
      KnowledgeBaseError("kb"),
      APIError("api"),
      ValidationError("validation"),
    ]

    for exc in exceptions_to_test:
      with pytest.raises(DejavuError):
        raise exc


if __name__ == "__main__":
  pytest.main([__file__])

# fin
