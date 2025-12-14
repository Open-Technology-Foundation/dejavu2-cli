"""
Unit tests for the conversations module in dejavu2-cli.
"""

import datetime
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import modules from the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from conversations import Conversation, ConversationManager, Message
from errors import ConversationError


class TestMessage:
  """Test the Message class."""

  def test_message_creation(self):
    """Test creating a message."""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert isinstance(msg.timestamp, datetime.datetime)

    # Test with explicit timestamp
    timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)
    msg = Message(role="assistant", content="Hi", timestamp=timestamp)
    assert msg.role == "assistant"
    assert msg.content == "Hi"
    assert msg.timestamp == timestamp

  def test_message_to_dict(self):
    """Test converting a message to a dictionary."""
    timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)
    msg = Message(role="system", content="You are a helpful assistant", timestamp=timestamp)

    msg_dict = msg.to_dict()
    assert msg_dict["role"] == "system"
    assert msg_dict["content"] == "You are a helpful assistant"
    assert msg_dict["timestamp"] == timestamp.isoformat()

  def test_message_from_dict(self):
    """Test creating a message from a dictionary."""
    timestamp_str = "2025-01-01T12:00:00"
    msg_dict = {"role": "user", "content": "What's the weather?", "timestamp": timestamp_str}

    msg = Message.from_dict(msg_dict)
    assert msg.role == "user"
    assert msg.content == "What's the weather?"
    assert msg.timestamp == datetime.datetime.fromisoformat(timestamp_str)


class TestConversation:
  """Test the Conversation class."""

  def test_conversation_creation(self):
    """Test creating a conversation."""
    # Test with minimal arguments
    conv = Conversation(id="test-id")
    assert conv.id == "test-id"
    assert conv.title is None
    assert conv.messages == []
    assert isinstance(conv.created_at, datetime.datetime)
    assert isinstance(conv.updated_at, datetime.datetime)
    assert conv.metadata == {}

    # Test with all arguments
    timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)
    msg = Message(role="user", content="Hello")
    conv = Conversation(
      id="full-test", title="Test Conversation", messages=[msg], created_at=timestamp, updated_at=timestamp, metadata={"tag": "test"}
    )

    assert conv.id == "full-test"
    assert conv.title == "Test Conversation"
    assert len(conv.messages) == 1
    assert conv.messages[0] == msg
    assert conv.created_at == timestamp
    assert conv.updated_at == timestamp
    assert conv.metadata == {"tag": "test"}

  def test_add_message(self):
    """Test adding a message to a conversation."""
    conv = Conversation(id="test-id")

    # Add a message
    msg = conv.add_message(role="user", content="Hello")

    assert len(conv.messages) == 1
    assert conv.messages[0] == msg
    assert conv.messages[0].role == "user"
    assert conv.messages[0].content == "Hello"

    # Verify updated_at gets updated
    old_updated_at = conv.updated_at

    # Wait a tiny bit so timestamps are different
    import time

    time.sleep(0.001)

    conv.add_message(role="assistant", content="Hi there")

    assert len(conv.messages) == 2
    assert conv.messages[1].role == "assistant"
    assert conv.messages[1].content == "Hi there"
    assert conv.updated_at > old_updated_at

  def test_to_dict(self):
    """Test converting a conversation to a dictionary."""
    timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)

    # Need to patch datetime.now to keep updated_at from changing
    with patch("datetime.datetime") as mock_datetime:
      # Set now() to return our fixed time
      mock_now = timestamp
      mock_datetime.now.return_value = mock_now
      # Keep other datetime functionality
      mock_datetime.fromisoformat = datetime.datetime.fromisoformat

      conv = Conversation(id="test-id", title="Test Conversation", created_at=timestamp, updated_at=timestamp, metadata={"tag": "test"})

      # Add message without changing the updated_at timestamp
      with patch.object(conv, "updated_at", timestamp):
        conv.add_message(role="user", content="Hello")

      conv_dict = conv.to_dict()

      assert conv_dict["id"] == "test-id"
      assert conv_dict["title"] == "Test Conversation"
      assert conv_dict["created_at"] == timestamp.isoformat()
      assert conv_dict["updated_at"] == timestamp.isoformat()
    assert conv_dict["metadata"] == {"tag": "test"}
    assert len(conv_dict["messages"]) == 1
    assert conv_dict["messages"][0]["role"] == "user"
    assert conv_dict["messages"][0]["content"] == "Hello"

  def test_from_dict(self):
    """Test creating a conversation from a dictionary."""
    timestamp_str = "2025-01-01T12:00:00"

    conv_dict = {
      "id": "test-id",
      "title": "Test Conversation",
      "created_at": timestamp_str,
      "updated_at": timestamp_str,
      "metadata": {"tag": "test"},
      "messages": [
        {"role": "system", "content": "You are a helpful assistant", "timestamp": timestamp_str},
        {"role": "user", "content": "Hello", "timestamp": timestamp_str},
      ],
    }

    conv = Conversation.from_dict(conv_dict)

    assert conv.id == "test-id"
    assert conv.title == "Test Conversation"
    assert conv.created_at == datetime.datetime.fromisoformat(timestamp_str)
    assert conv.updated_at == datetime.datetime.fromisoformat(timestamp_str)
    assert conv.metadata == {"tag": "test"}
    assert len(conv.messages) == 2
    assert conv.messages[0].role == "system"
    assert conv.messages[0].content == "You are a helpful assistant"
    assert conv.messages[1].role == "user"
    assert conv.messages[1].content == "Hello"

  def test_get_messages_for_llm(self):
    """Test getting messages formatted for LLM API calls."""
    conv = Conversation(id="test-id")

    # Add messages of different types
    conv.add_message(role="system", content="You are a helpful assistant")
    conv.add_message(role="user", content="Hello")
    conv.add_message(role="assistant", content="Hi there")

    # Get all messages (default)
    messages = conv.get_messages_for_llm()
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a helpful assistant"

    # Get non-system messages only
    messages = conv.get_messages_for_llm(include_system=False)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

  def test_extract_message_history(self):
    """Test extracting message history as a formatted string."""
    conv = Conversation(id="test-id")

    # Add messages of different types
    conv.add_message(role="system", content="You are a helpful assistant")
    conv.add_message(role="user", content="Hello")
    conv.add_message(role="assistant", content="Hi there")
    conv.add_message(role="user", content="How are you?")
    conv.add_message(role="assistant", content="I'm doing well!")

    # Get complete history (should exclude system message)
    history = conv.extract_message_history()
    assert "You are a helpful assistant" not in history
    assert "User: Hello" in history
    assert "Assistant: Hi there" in history
    assert "User: How are you?" in history
    assert "Assistant: I'm doing well!" in history

    # Test with max_messages limit
    history = conv.extract_message_history(max_messages=2)
    assert "User: Hello" not in history
    assert "Assistant: Hi there" not in history
    assert "User: How are you?" in history
    assert "Assistant: I'm doing well!" in history


class TestConversationManager:
  """Test the ConversationManager class."""

  def test_init(self):
    """Test initializing the conversation manager."""
    # Test with default storage directory
    with patch("os.path.expanduser", return_value="/mock/home"), patch("pathlib.Path.mkdir") as mock_mkdir:
      manager = ConversationManager()
      assert manager.storage_dir == Path("/mock/home/.config/dejavu2-cli/conversations")
      assert manager.active_conversation is None
      mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    # Test with custom storage directory
    with patch("pathlib.Path.mkdir") as mock_mkdir:
      manager = ConversationManager(storage_dir="/tmp/test-conversations")
      assert manager.storage_dir == Path("/tmp/test-conversations")
      mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

  def test_new_conversation(self):
    """Test creating a new conversation."""
    with patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir="/tmp/test-conversations")

      with patch("uuid.uuid4", return_value="test-uuid-1234"):
        # Test with minimal arguments
        conv = manager.new_conversation()
        assert conv.id == "test-uuid-1234"  # UUID4 is generated
        assert conv.title is None
        assert len(conv.messages) == 0
        assert manager.active_conversation == conv
        assert conv.metadata == {}  # Empty metadata by default

        # Test with system prompt
        conv = manager.new_conversation(system_prompt="You are a helpful assistant")
        assert len(conv.messages) == 1
        assert conv.messages[0].role == "system"
        assert conv.messages[0].content == "You are a helpful assistant"

        # Test with title
        conv = manager.new_conversation(title="Test Conversation")
        assert conv.title == "Test Conversation"

        # Test with metadata
        model_metadata = {"model": "claude-3-5-sonnet", "temperature": 0.7, "max_tokens": 4000}
        conv = manager.new_conversation(title="Conversation With Metadata", metadata=model_metadata)
        assert conv.metadata == model_metadata

  def test_save_and_load_conversation(self):
    """Test saving and loading a conversation."""
    # Use a simple implementation with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir, patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir=temp_dir)

      # Create a conversation with a fixed ID
      with patch("uuid.uuid4", return_value="test-id"):
        conv = manager.new_conversation(title="Test Save/Load")

      # Add messages
      with patch("datetime.datetime") as mock_dt:
        timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)
        mock_dt.now.return_value = timestamp
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi there")

      # Write to the temporary directory
      conv_path = os.path.join(temp_dir, "test-id.json")
      conv_data = conv.to_dict()
      with open(conv_path, "w") as f:
        json.dump(conv_data, f)

      # Reset manager and reload
      manager.active_conversation = None
      loaded_conv = manager.load_conversation("test-id")

      # Verify
      assert loaded_conv is not None
      assert loaded_conv.id == "test-id"
      assert loaded_conv.title == "Test Save/Load"
      assert len(loaded_conv.messages) == 2
      assert loaded_conv.messages[0].role == "user"
      assert loaded_conv.messages[0].content == "Hello"
      assert loaded_conv.messages[1].role == "assistant"
      assert loaded_conv.messages[1].content == "Hi there"
      assert manager.active_conversation == loaded_conv

  def test_list_conversations(self):
    """Test listing all stored conversations."""
    with tempfile.TemporaryDirectory() as temp_dir, patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir=temp_dir)

      # Create conversation files directly
      conv1_data = {
        "id": "conv1",
        "title": "First Conversation",
        "created_at": "2025-01-01T12:00:00",
        "updated_at": "2025-01-01T12:10:00",
        "metadata": {},
        "messages": [],
      }

      conv2_data = {
        "id": "conv2",
        "title": "Second Conversation",
        "created_at": "2025-01-01T12:20:00",
        "updated_at": "2025-01-01T12:30:00",
        "metadata": {},
        "messages": [],
      }

      # Create files in temp directory
      with open(os.path.join(temp_dir, "conv1.json"), "w") as f:
        json.dump(conv1_data, f)

      with open(os.path.join(temp_dir, "conv2.json"), "w") as f:
        json.dump(conv2_data, f)

      # List conversations
      with patch("os.path.getmtime") as mock_getmtime:
        # Mock getmtime to return values that will sort conv2 first
        mock_getmtime.side_effect = lambda path: 200 if "conv2" in str(path) else 100

        conversations = manager.list_conversations()

        assert len(conversations) == 2
        # Latest conversation should be first (sorted by mtime)
        assert conversations[0]["id"] == "conv2"
        assert conversations[0]["title"] == "Second Conversation"
        assert conversations[1]["id"] == "conv1"
        assert conversations[1]["title"] == "First Conversation"

  def test_delete_conversation(self):
    """Test deleting a conversation."""
    with tempfile.TemporaryDirectory() as temp_dir, patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir=temp_dir)

      # Create a conversation
      with patch("uuid.uuid4", return_value="test-id"):
        conv = manager.new_conversation(title="To Be Deleted")

      # Create file directly
      conv_path = os.path.join(temp_dir, "test-id.json")
      with open(conv_path, "w") as f:
        json.dump(conv.to_dict(), f)

      # Verify it exists
      assert os.path.exists(conv_path)

      # Delete it (should not raise exception)
      manager.delete_conversation("test-id")

      # Verify it's gone
      assert not os.path.exists(conv_path)

      # Test deleting a non-existent conversation
      with pytest.raises(ConversationError):
        manager.delete_conversation("non-existent-id")

  def test_get_most_recent_conversation(self):
    """Test getting the most recent conversation."""
    with tempfile.TemporaryDirectory() as temp_dir, patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir=temp_dir)

      # Create conversation files directly
      conv1_data = {
        "id": "conv1",
        "title": "Older Conversation",
        "created_at": "2025-01-01T12:00:00",
        "updated_at": "2025-01-01T12:10:00",
        "metadata": {},
        "messages": [],
      }

      conv2_data = {
        "id": "conv2",
        "title": "Newer Conversation",
        "created_at": "2025-01-01T12:20:00",
        "updated_at": "2025-01-01T12:30:00",
        "metadata": {},
        "messages": [],
      }

      # Create files in temp directory
      with open(os.path.join(temp_dir, "conv1.json"), "w") as f:
        json.dump(conv1_data, f)

      with open(os.path.join(temp_dir, "conv2.json"), "w") as f:
        json.dump(conv2_data, f)

      # Mock list_conversations to return conv2 as most recent
      with patch.object(manager, "list_conversations") as mock_list:
        mock_list.return_value = [
          {"id": "conv2", "title": "Newer Conversation", "created_at": "2025-01-01T12:20:00", "updated_at": "2025-01-01T12:30:00"},
          {"id": "conv1", "title": "Older Conversation", "created_at": "2025-01-01T12:00:00", "updated_at": "2025-01-01T12:10:00"},
        ]

        # Mock load_conversation to return a properly constructed conversation
        with patch.object(manager, "load_conversation") as mock_load:
          conv = Conversation(
            id="conv2",
            title="Newer Conversation",
            created_at=datetime.datetime.fromisoformat("2025-01-01T12:20:00"),
            updated_at=datetime.datetime.fromisoformat("2025-01-01T12:30:00"),
          )
          mock_load.return_value = conv

          # Get most recent
          recent = manager.get_most_recent_conversation()

          assert recent is not None
          assert recent.id == "conv2"
          assert recent.title == "Newer Conversation"
          mock_load.assert_called_with("conv2")

  def test_suggest_title_from_content(self):
    """Test generating a title based on conversation content."""
    manager = ConversationManager()

    # Create a conversation with content
    conv = Conversation(id="test-id")
    conv.add_message(role="system", content="You are a helpful assistant")
    conv.add_message(role="user", content="Tell me about quantum computing")
    conv.add_message(role="assistant", content="Quantum computing is a type of computing that uses quantum mechanics...")

    # Mock the query function
    mock_query_func = MagicMock(return_value="Quantum Computing Basics")

    # Generate a title
    title = manager.suggest_title_from_content(conv, mock_query_func)

    assert title == "Quantum Computing Basics"
    assert mock_query_func.called

    # Check that the prompt includes content from the conversation
    call_args = mock_query_func.call_args[0][0]
    assert "Tell me about quantum computing" in call_args
    assert "Quantum computing is a type" in call_args

    # Test with empty conversation
    empty_conv = Conversation(id="empty")
    title = manager.suggest_title_from_content(empty_conv, mock_query_func)
    assert title == "Untitled Conversation"  # Default title for empty conversations

  def test_list_conversation_messages(self):
    """Test listing messages in a conversation with indices."""
    with tempfile.TemporaryDirectory() as temp_dir, patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir=temp_dir)

      # Create a test conversation
      with patch("uuid.uuid4", return_value="test-msg-id"), patch("datetime.datetime") as mock_dt:
        timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)
        mock_dt.now.return_value = timestamp
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        # Create a conversation with various messages
        conv = Conversation(id="test-msg-id")
        conv.add_message("system", "You are a helpful assistant")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there")
        conv.add_message("user", "Tell me about Python")

        # Save the conversation
        manager.active_conversation = conv
        conv_path = os.path.join(temp_dir, "test-msg-id.json")
        with open(conv_path, "w") as f:
          json.dump(conv.to_dict(), f)

      # List the messages
      messages = manager.list_conversation_messages("test-msg-id")

      # Check if messages are listed with correct indices
      assert len(messages) == 4
      assert messages[0]["index"] == 0
      assert messages[0]["role"] == "system"
      assert messages[0]["is_system"] is True
      assert "You are a helpful assistant" in messages[0]["content_preview"]

      assert messages[1]["index"] == 1
      assert messages[1]["role"] == "user"
      assert messages[1]["is_system"] is False
      assert "Hello" in messages[1]["content_preview"]

      assert messages[2]["index"] == 2
      assert messages[2]["role"] == "assistant"
      assert messages[2]["is_system"] is False
      assert "Hi there" in messages[2]["content_preview"]

      assert messages[3]["index"] == 3
      assert messages[3]["role"] == "user"
      assert "Tell me about Python" in messages[3]["content_preview"]

      # Test with nonexistent conversation
      with pytest.raises(ConversationError):
        manager.list_conversation_messages("nonexistent-id")

  def test_remove_message_functions(self):
    """Test removing messages and message pairs from conversations."""
    with tempfile.TemporaryDirectory() as temp_dir, patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir=temp_dir)

      # Create a test conversation
      with patch("uuid.uuid4", return_value="test-remove-id"), patch("datetime.datetime") as mock_dt:
        timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)
        mock_dt.now.return_value = timestamp
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        # Create a conversation with various messages
        conv = Conversation(id="test-remove-id")
        conv.add_message("system", "You are a helpful assistant")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there")
        conv.add_message("user", "Tell me about Python")
        conv.add_message("assistant", "Python is a programming language...")

        # Save the conversation
        manager.active_conversation = conv
        conv_path = os.path.join(temp_dir, "test-remove-id.json")
        with open(conv_path, "w") as f:
          json.dump(conv.to_dict(), f)

      # Test removing a single message (should not raise exception)
      manager.remove_message_at_index("test-remove-id", 2)

      # Verify message was removed by listing messages
      messages = manager.list_conversation_messages("test-remove-id")
      assert len(messages) == 4
      assert messages[2]["role"] == "user"
      assert "Tell me about Python" in messages[2]["content_preview"]

      # Test removing a message pair (should not raise exception)
      manager.remove_message_pair("test-remove-id", 2)

      # Verify pair was removed
      messages = manager.list_conversation_messages("test-remove-id")
      assert len(messages) == 2
      assert messages[0]["role"] == "system"
      assert messages[1]["role"] == "user"
      assert "Hello" in messages[1]["content_preview"]

      # Test with invalid indices
      with pytest.raises(ConversationError):
        manager.remove_message_at_index("test-remove-id", 99)

      # Test with nonexistent conversation
      with pytest.raises(ConversationError):
        manager.remove_message_pair("nonexistent-id", 0)

  def test_remove_message_at_index(self):
    """Test removing a message at a specific index."""
    conv = Conversation(id="test-id")

    # Add some messages
    conv.add_message("system", "You are a helpful assistant")
    conv.add_message("user", "Hello")
    conv.add_message("assistant", "Hi there")
    conv.add_message("user", "How are you?")

    assert len(conv.messages) == 4

    # Remove a message in the middle
    result = conv.remove_message_at_index(2)
    assert result is True
    assert len(conv.messages) == 3
    assert conv.messages[0].role == "system"
    assert conv.messages[1].role == "user"
    assert conv.messages[1].content == "Hello"
    assert conv.messages[2].role == "user"
    assert conv.messages[2].content == "How are you?"

    # Try removing with an invalid index
    result = conv.remove_message_at_index(10)
    assert result is False
    assert len(conv.messages) == 3  # No change

    # Remove the first message
    result = conv.remove_message_at_index(0)
    assert result is True
    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[0].content == "Hello"

  def test_remove_message_pair(self):
    """Test removing a user-assistant message pair."""
    conv = Conversation(id="test-id")

    # Add messages forming conversation pairs
    conv.add_message("system", "You are a helpful assistant")
    conv.add_message("user", "Hello")
    conv.add_message("assistant", "Hi there")
    conv.add_message("user", "How are you?")
    conv.add_message("assistant", "I'm doing well!")

    assert len(conv.messages) == 5

    # Remove the second pair (user: "How are you?" -> assistant: "I'm doing well!")
    result = conv.remove_message_pair(3)
    assert result is True
    assert len(conv.messages) == 3
    assert conv.messages[0].role == "system"
    assert conv.messages[1].role == "user"
    assert conv.messages[1].content == "Hello"
    assert conv.messages[2].role == "assistant"
    assert conv.messages[2].content == "Hi there"

    # Try removing with an invalid index (out of bounds)
    result = conv.remove_message_pair(10)
    assert result is False
    assert len(conv.messages) == 3  # No change

    # Try removing with a non-user message index
    result = conv.remove_message_pair(0)  # System message
    assert result is False
    assert len(conv.messages) == 3  # No change

    # Remove the remaining pair
    result = conv.remove_message_pair(1)  # user: "Hello"
    assert result is True
    assert len(conv.messages) == 1
    assert conv.messages[0].role == "system"

  def test_conversation_to_markdown(self):
    """Test exporting a conversation to markdown format."""
    # Create a test conversation with all types of messages
    timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)
    metadata = {"model": "claude-3-5-sonnet", "temperature": 0.7, "max_tokens": 4000}

    conv = Conversation(id="test-md-export", title="Markdown Export Test", created_at=timestamp, updated_at=timestamp, metadata=metadata)

    # Add different types of messages with fixed timestamps
    msg_timestamp = timestamp  # Keep same timestamp for consistency

    # Create messages directly to set fixed timestamps
    sys_msg = Message(role="system", content="You are a helpful assistant.", timestamp=msg_timestamp)
    user_msg = Message(role="user", content="Tell me about markdown.", timestamp=msg_timestamp)
    asst_msg = Message(role="assistant", content="Markdown is a lightweight markup language...", timestamp=msg_timestamp)

    # Add messages directly to conversation list
    conv.messages = [sys_msg, user_msg, asst_msg]

    # Export to markdown
    markdown = conv.to_markdown()

    # Verify content
    assert "# Markdown Export Test" in markdown
    assert "*Conversation ID: `test-md-export`*" in markdown
    assert "*Created: 2025-01-01 12:00*" in markdown
    assert "*Updated: 2025-01-01 12:00*" in markdown

    # Check metadata section
    assert "## Metadata" in markdown
    assert "**model**: claude-3-5-sonnet" in markdown
    assert "**temperature**: 0.7" in markdown
    assert "**max_tokens**: 4000" in markdown

    # Check conversation content
    assert "## Conversation" in markdown
    assert "<details>" in markdown
    assert "<summary>System Prompt</summary>" in markdown
    assert "You are a helpful assistant." in markdown
    assert "### User" in markdown
    assert "Tell me about markdown." in markdown
    assert "### Assistant" in markdown
    assert "Markdown is a lightweight markup language" in markdown
    assert "---" in markdown  # Check for separator between messages

  def test_export_conversation_to_markdown(self):
    """Test exporting a conversation to a markdown file."""
    with tempfile.TemporaryDirectory() as temp_dir, patch("pathlib.Path.mkdir"):
      manager = ConversationManager(storage_dir=temp_dir)

      # Create a test conversation with fixed timestamps
      timestamp = datetime.datetime(2025, 1, 1, 12, 0, 0)

      # Create the conversation directly with fixed timestamps
      conv = Conversation(
        id="test-md-id", title="Export Test", created_at=timestamp, updated_at=timestamp, metadata={"model": "test-model", "temperature": 0.7}
      )

      # Create messages with fixed timestamps
      sys_msg = Message(role="system", content="You are a helpful assistant.", timestamp=timestamp)
      user_msg = Message(role="user", content="Hello", timestamp=timestamp)
      asst_msg = Message(role="assistant", content="Hi there!", timestamp=timestamp)

      # Add messages directly to conversation
      conv.messages = [sys_msg, user_msg, asst_msg]

      # Set as active conversation
      manager.active_conversation = conv

      # Save the conversation
      # Create conv file directly to avoid timestamp issues
      conv_path = os.path.join(temp_dir, "test-md-id.json")
      with open(conv_path, "w") as f:
        json.dump(conv.to_dict(), f)

      # Create a temporary file for the export
      export_path = os.path.join(temp_dir, "export_test.md")

      # Test exporting active conversation
      result = manager.export_conversation_to_markdown(output_path=export_path)
      assert result == export_path
      assert os.path.exists(export_path)

      # Verify content
      with open(export_path, encoding="utf-8") as f:
        content = f.read()
        assert "# Export Test" in content
        assert "*Conversation ID: `test-md-id`*" in content
        assert "**model**: test-model" in content
        assert "You are a helpful assistant." in content
        assert "Hello" in content
        assert "Hi there!" in content

      # Test exporting by ID
      os.remove(export_path)  # Delete the previous export
      result = manager.export_conversation_to_markdown(conv_id="test-md-id", output_path=export_path)
      assert result == export_path
      assert os.path.exists(export_path)

      # Test exporting with non-existent ID
      with pytest.raises(ConversationError):
        manager.export_conversation_to_markdown(conv_id="non-existent-id", output_path=export_path)

      # Test exporting without saving to file (just return content)
      content = manager.export_conversation_to_markdown(conv_id="test-md-id")
      assert isinstance(content, str)
      assert "# Export Test" in content
