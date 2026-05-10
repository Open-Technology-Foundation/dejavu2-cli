"""
Unit tests for main module functionality in dejavu2-cli.
"""

import os

# Import functions from the application
import sys
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import main


class TestMain:
  """Test main CLI functionality."""

  def setUp(self):
    """Set up test fixtures."""
    self.runner = CliRunner()

  def test_main_help(self):
    """Test that help command works."""
    runner = CliRunner()
    result = runner.invoke(main.main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output

  def test_main_version(self):
    """Test version flag."""
    runner = CliRunner()
    result = runner.invoke(main.main, ["--version"])
    assert result.exit_code == 0
    assert "dejavu2-cli" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  @patch("models.get_canonical_model")
  @patch("llm_clients.get_api_keys")
  @patch("llm_clients.initialize_clients")
  @patch("llm_clients.query")
  def test_main_simple_query(self, mock_query, mock_init_clients, mock_get_keys, mock_get_model, mock_conv_manager, mock_load_config):
    """Test a simple query execution."""
    # Setup mocks
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.new_conversation.return_value = MagicMock()

    mock_get_model.return_value = ("gpt-4o", {"model": "gpt-4o", "parent": "openai", "apikey": "OPENAI_API_KEY", "api_key_valid": True})

    mock_get_keys.return_value = {"OPENAI_API_KEY": "test-key"}
    mock_init_clients.return_value = {"openai": MagicMock()}
    mock_query.return_value = "Test response"

    runner = CliRunner()
    result = runner.invoke(main.main, ["Test query"])

    assert result.exit_code == 0
    assert mock_query.called

  @patch("config.load_config")
  @patch("models.list_models")
  def test_main_list_models(self, mock_list_models, mock_load_config):
    """Test listing models."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    runner = CliRunner()
    result = runner.invoke(main.main, ["--list-models"])

    assert result.exit_code == 0
    mock_list_models.assert_called_once()

  @patch("config.load_config")
  @patch("templates.list_templates")
  def test_main_list_templates(self, mock_list_templates, mock_load_config):
    """Test listing templates."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    runner = CliRunner()
    result = runner.invoke(main.main, ["--list-template", "all"])

    assert result.exit_code == 0
    mock_list_templates.assert_called_once_with(os.path.join(main.SCRIPT_DIR, "Agents.json"), "all")

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_list_conversations(self, mock_conv_manager, mock_load_config):
    """Test listing conversations."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.list_conversations.return_value = []

    runner = CliRunner()
    result = runner.invoke(main.main, ["--list-conversations"])

    assert result.exit_code == 0
    assert "No saved conversations found." in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_delete_conversation(self, mock_conv_manager, mock_load_config):
    """Test deleting a conversation."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.delete_conversation.return_value = True

    runner = CliRunner()
    result = runner.invoke(main.main, ["--delete-conversation", "test-id"])

    assert result.exit_code == 0
    assert "Conversation test-id deleted." in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  @patch("models.get_canonical_model")
  @patch("llm_clients.get_api_keys")
  @patch("llm_clients.initialize_clients")
  @patch("display.display_status")
  def test_main_status(self, mock_display, mock_init_clients, mock_get_keys, mock_get_model, mock_conv_manager, mock_load_config):
    """Test status display."""
    # Setup mocks
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance

    mock_get_model.return_value = ("gpt-4o", {"model": "gpt-4o", "parent": "openai", "apikey": "OPENAI_API_KEY", "api_key_valid": True})

    mock_get_keys.return_value = {"OPENAI_API_KEY": "test-key"}
    mock_init_clients.return_value = {"openai": MagicMock()}

    runner = CliRunner()
    result = runner.invoke(main.main, ["--status", "Test query"])

    assert result.exit_code == 0
    mock_display.assert_called_once()

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  @patch("templates.get_template")
  @patch("models.get_canonical_model")
  @patch("llm_clients.get_api_keys")
  @patch("llm_clients.initialize_clients")
  @patch("llm_clients.query")
  def test_main_with_template(
    self, mock_query, mock_init_clients, mock_get_keys, mock_get_model, mock_get_template, mock_conv_manager, mock_load_config
  ):
    """Test query with template."""
    # Setup mocks
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_get_template.return_value = (
      "test_template",
      {"model": "claude-3-5-sonnet", "temperature": 0.5, "systemprompt": "You are a test assistant."},
    )

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.new_conversation.return_value = MagicMock()

    mock_get_model.return_value = (
      "claude-3-5-sonnet",
      {"model": "claude-3-5-sonnet", "parent": "anthropic", "apikey": "ANTHROPIC_API_KEY", "api_key_valid": True},
    )

    mock_get_keys.return_value = {"ANTHROPIC_API_KEY": "test-key"}
    mock_init_clients.return_value = {"anthropic": MagicMock()}
    mock_query.return_value = "Template response"

    runner = CliRunner()
    result = runner.invoke(main.main, ["--template", "test_template", "Test query"])

    assert result.exit_code == 0
    mock_get_template.assert_called_once()
    mock_query.assert_called_once()

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  @patch("models.get_canonical_model")
  @patch("llm_clients.get_api_keys")
  @patch("llm_clients.initialize_clients")
  @patch("context.get_reference_string")
  @patch("llm_clients.query")
  def test_main_with_reference(self, mock_query, mock_get_ref, mock_init_clients, mock_get_keys, mock_get_model, mock_conv_manager, mock_load_config):
    """Test query with reference files."""
    # Setup mocks
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.new_conversation.return_value = MagicMock()

    mock_get_model.return_value = ("gpt-4o", {"model": "gpt-4o", "parent": "openai", "apikey": "OPENAI_API_KEY", "api_key_valid": True})

    mock_get_keys.return_value = {"OPENAI_API_KEY": "test-key"}
    mock_init_clients.return_value = {"openai": MagicMock()}
    mock_get_ref.return_value = '<reference name="test">Test content</reference>'
    mock_query.return_value = "Reference response"

    runner = CliRunner()
    result = runner.invoke(main.main, ["--reference", "test.txt", "Test query"])

    assert result.exit_code == 0
    mock_get_ref.assert_called_once_with("test.txt")
    mock_query.assert_called_once()

  @patch("config.load_config")
  @patch("models.get_canonical_model")
  def test_main_invalid_model(self, mock_get_model, mock_load_config):
    """Test behavior with invalid model."""
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_get_model.return_value = (None, {})

    runner = CliRunner()
    result = runner.invoke(main.main, ["--model", "invalid-model", "Test query"])

    assert result.exit_code == 1
    # Changed error message when model is None
    assert "Model name cannot be None or empty" in result.output

  def test_main_no_query(self):
    """Test behavior when no query is provided."""
    runner = CliRunner()
    result = runner.invoke(main.main, [])

    assert result.exit_code == 1
    assert "Require at least one query" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_export_conversation(self, mock_conv_manager, mock_load_config):
    """Test exporting a conversation."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.export_conversation_to_markdown.return_value = "# Conversation\\n\\nContent"

    runner = CliRunner()
    result = runner.invoke(main.main, ["--export-conversation", "test-id", "--stdout"])

    assert result.exit_code == 0
    assert "# Conversation" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  @patch("models.get_canonical_model")
  @patch("llm_clients.get_api_keys")
  @patch("llm_clients.initialize_clients")
  @patch("llm_clients.query")
  def test_main_continue_conversation(self, mock_query, mock_init_clients, mock_get_keys, mock_get_model, mock_conv_manager, mock_load_config):
    """Test continuing an existing conversation."""
    # Setup mocks
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance

    # Mock an existing conversation
    mock_conversation = MagicMock()
    mock_conversation.messages = []
    mock_conversation.get_messages_for_llm.return_value = []
    mock_conv_manager_instance.get_most_recent_conversation.return_value = mock_conversation

    mock_get_model.return_value = ("gpt-4o", {"model": "gpt-4o", "parent": "openai", "apikey": "OPENAI_API_KEY", "api_key_valid": True})

    mock_get_keys.return_value = {"OPENAI_API_KEY": "test-key"}
    mock_init_clients.return_value = {"openai": MagicMock()}
    mock_query.return_value = "Continued response"

    runner = CliRunner()
    result = runner.invoke(main.main, ["--continue", "Continue query"])

    assert result.exit_code == 0
    mock_conv_manager_instance.get_most_recent_conversation.assert_called_once()
    mock_query.assert_called_once()

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_continue_no_previous_conversations(self, mock_conv_manager, mock_load_config):
    """Test continuing when no previous conversations exist."""
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    # No previous conversations
    mock_conv_manager_instance.get_most_recent_conversation.return_value = None

    runner = CliRunner()
    result = runner.invoke(main.main, ["--continue", "Test query"])

    # Should still proceed but print a warning
    assert "No previous conversations found to continue" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_conversation_not_found(self, mock_conv_manager, mock_load_config):
    """Test loading a non-existent conversation by ID."""
    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    # Conversation not found
    mock_conv_manager_instance.load_conversation.return_value = None

    runner = CliRunner()
    result = runner.invoke(main.main, ["--conversation", "nonexistent-id", "Test query"])

    assert result.exit_code == 1
    assert "Conversation nonexistent-id not found" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_delete_conversation_not_found(self, mock_conv_manager, mock_load_config):
    """Test deleting a conversation that doesn't exist."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.delete_conversation.return_value = False

    runner = CliRunner()
    result = runner.invoke(main.main, ["--delete-conversation", "nonexistent-id"])

    assert result.exit_code == 0
    assert "Conversation nonexistent-id not found" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_export_conversation_no_conversations(self, mock_conv_manager, mock_load_config):
    """Test exporting when no conversations exist."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.active_conversation = None
    mock_conv_manager_instance.get_most_recent_conversation.return_value = None

    runner = CliRunner()
    result = runner.invoke(main.main, ["--export-conversation", "current", "--stdout"])

    assert result.exit_code == 0
    assert "No conversations found to export" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_export_conversation_error(self, mock_conv_manager, mock_load_config):
    """Test export conversation with error."""
    from errors import ConversationError

    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.export_conversation_to_markdown.side_effect = ConversationError("Export failed")

    runner = CliRunner()
    result = runner.invoke(main.main, ["--export-conversation", "test-id", "--stdout"])

    assert result.exit_code == 1
    assert "Conversation error: Export failed" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_remove_message(self, mock_conv_manager, mock_load_config):
    """Test removing a specific message from conversation."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance

    runner = CliRunner()
    result = runner.invoke(main.main, ["--remove-message", "test-conv-id", "5"])

    assert result.exit_code == 0
    mock_conv_manager_instance.remove_message_at_index.assert_called_once_with("test-conv-id", 5)

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_remove_message_error(self, mock_conv_manager, mock_load_config):
    """Test removing a message with error."""
    from errors import ConversationError

    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance
    mock_conv_manager_instance.remove_message_at_index.side_effect = ConversationError("Message not found")

    runner = CliRunner()
    result = runner.invoke(main.main, ["--remove-message", "test-conv-id", "999"])

    assert result.exit_code == 0
    assert "Conversation error: Message not found" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_remove_pair(self, mock_conv_manager, mock_load_config):
    """Test removing a message pair from conversation."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance

    runner = CliRunner()
    result = runner.invoke(main.main, ["--remove-pair", "test-conv-id", "4"])

    assert result.exit_code == 0
    mock_conv_manager_instance.remove_message_pair.assert_called_once_with("test-conv-id", 4)

  @patch("config.load_config")
  @patch("templates.get_template")
  @patch("models.get_canonical_model")
  def test_main_template_error(self, mock_get_model, mock_get_template, mock_load_config):
    """Test template error handling."""
    from errors import TemplateError

    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_get_template.side_effect = TemplateError("Template not found: invalid_template")

    runner = CliRunner()
    result = runner.invoke(main.main, ["--template", "invalid_template", "Test query"])

    assert result.exit_code == 1
    assert "Template error: Template not found" in result.output

  @patch("config.load_config")
  @patch("models.get_canonical_model")
  def test_main_model_error(self, mock_get_model, mock_load_config):
    """Test model error handling."""
    from errors import ModelError

    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_get_model.side_effect = ModelError("Model not found: invalid_model")

    runner = CliRunner()
    result = runner.invoke(main.main, ["--model", "invalid_model", "Test query"])

    assert result.exit_code == 1
    assert "Model error: Model not found" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  @patch("models.get_canonical_model")
  @patch("llm_clients.get_api_keys")
  @patch("llm_clients.initialize_clients")
  @patch("context.get_reference_string")
  @patch("llm_clients.query")
  def test_main_reference_error(self, mock_query, mock_get_ref, mock_init_clients, mock_get_keys, mock_get_model, mock_conv_manager, mock_load_config):
    """Test reference file error handling."""
    from errors import ReferenceError

    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_get_model.return_value = ("gpt-4o", {"model": "gpt-4o", "parent": "openai", "apikey": "OPENAI_API_KEY", "api_key_valid": True})
    mock_get_ref.side_effect = ReferenceError("Cannot read reference file: nonexistent.txt")

    runner = CliRunner()
    result = runner.invoke(main.main, ["--reference", "nonexistent.txt", "Test query"])

    assert result.exit_code == 1
    assert "Reference error: Cannot read reference file" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  @patch("models.get_canonical_model")
  @patch("llm_clients.get_api_keys")
  @patch("llm_clients.initialize_clients")
  @patch("context.get_knowledgebase_string")
  @patch("llm_clients.query")
  def test_main_knowledgebase_error(
    self, mock_query, mock_get_kb, mock_init_clients, mock_get_keys, mock_get_model, mock_conv_manager, mock_load_config
  ):
    """Test knowledgebase error handling."""
    from errors import KnowledgeBaseError

    mock_load_config.return_value = {
      "defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000, "template": None},
      "paths": {"template_path": "Agents.json"},
    }

    mock_get_model.return_value = ("gpt-4o", {"model": "gpt-4o", "parent": "openai", "apikey": "OPENAI_API_KEY", "api_key_valid": True})
    mock_get_kb.side_effect = KnowledgeBaseError("Knowledgebase not found: invalid_kb")

    runner = CliRunner()
    result = runner.invoke(main.main, ["--knowledgebase", "invalid_kb", "Test query"])

    assert result.exit_code == 1
    assert "Knowledgebase error: Knowledgebase not found" in result.output

  @patch("config.load_config")
  @patch("context.list_knowledge_bases")
  def test_main_list_knowledge_bases_error(self, mock_list_kb, mock_load_config):
    """Test knowledge base listing error handling."""
    from errors import KnowledgeBaseError

    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}
    mock_list_kb.side_effect = KnowledgeBaseError("Directory not valid")

    runner = CliRunner()
    result = runner.invoke(main.main, ["--list-knowledge-bases"])

    assert result.exit_code == 1
    assert "Knowledgebase error: Directory not valid" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_list_messages(self, mock_conv_manager, mock_load_config):
    """Test listing messages in a conversation."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance

    # Mock conversation with messages
    mock_conversation = MagicMock()
    mock_conversation.title = "Test Conversation"
    mock_conv_manager_instance.load_conversation.return_value = mock_conversation

    mock_messages = [
      {"index": 0, "role": "user", "is_system": False, "timestamp": "2025-01-01 12:00:00", "content_preview": "Hello there"},
      {"index": 1, "role": "assistant", "is_system": False, "timestamp": "2025-01-01 12:00:05", "content_preview": "Hi! How can I help?"},
    ]
    mock_conv_manager_instance.list_conversation_messages.return_value = mock_messages

    runner = CliRunner()
    result = runner.invoke(main.main, ["--list-messages", "test-conv-id"])

    assert result.exit_code == 0
    assert "Test Conversation" in result.output
    assert "Hello there" in result.output
    assert "Hi! How can I help?" in result.output

  @patch("config.load_config")
  @patch("conversations.ConversationManager")
  def test_main_list_conversations_with_data(self, mock_conv_manager, mock_load_config):
    """Test listing conversations with formatted dates."""
    mock_load_config.return_value = {"defaults": {"model": "gpt-4o"}, "paths": {"template_path": "Agents.json"}}

    mock_conv_manager_instance = MagicMock()
    mock_conv_manager.return_value = mock_conv_manager_instance

    # Mock conversation data with ISO format dates
    mock_conversations = [
      {
        "id": "conv-123",
        "title": "First Conversation",
        "message_count": 5,
        "created_at": "2025-01-01T12:00:00",
        "updated_at": "2025-01-01T13:30:00",
      },
      {
        "id": "conv-456",
        "title": "Second Conversation",
        "message_count": 10,
        "created_at": "2025-01-02T09:00:00",
        "updated_at": "2025-01-02T10:15:00",
      },
    ]
    mock_conv_manager_instance.list_conversations.return_value = mock_conversations

    runner = CliRunner()
    result = runner.invoke(main.main, ["--list-conversations"])

    assert result.exit_code == 0
    assert "SAVED CONVERSATIONS" in result.output
    assert "conv-123" in result.output
    assert "First Conversation" in result.output
    assert "conv-456" in result.output
    assert "Second Conversation" in result.output
    assert "Messages: 5" in result.output
    assert "Messages: 10" in result.output


# fin
