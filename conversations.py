#!/usr/bin/env python3
"""
Conversation management module for dejavu2-cli.

This module handles the storage, retrieval, and manipulation of conversation
history for maintaining context across multiple queries.

Key Features:
- Persistent JSON storage with file locking (fcntl) for concurrent access safety
- Conversation metadata tracking (model, temperature, timestamps)
- Message pair removal for conversation history editing
- Markdown export for conversation archival
- LLM-assisted title generation

Classes:
- Message: Single message with role, content, and timestamp
- Conversation: Collection of messages with metadata
- ConversationManager: Storage operations with file locking
"""

import fcntl
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from errors import ConversationError

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class Message:
  """Represents a single message in a conversation."""

  role: str  # "user", "assistant", or "system"
  content: str
  timestamp: datetime | None = None

  def __post_init__(self) -> None:
    if self.timestamp is None:
      self.timestamp = datetime.now()

    # Ensure content is always a string
    if not isinstance(self.content, str):
      if hasattr(self.content, "text"):
        self.content = self.content.text
      elif isinstance(self.content, list | dict):
        self.content = str(self.content)
      else:
        self.content = str(self.content)

  def to_dict(self) -> dict[str, Any]:
    """Convert message to a dictionary for serialization."""
    # Ensure content is always a string for JSON serialization
    content_str = self.content
    if not isinstance(self.content, str):
      # Handle non-string content by converting to string
      if hasattr(self.content, "text"):
        content_str = self.content.text
      elif isinstance(self.content, list | dict):
        content_str = str(self.content)
      else:
        content_str = str(self.content)

    return {"role": self.role, "content": content_str, "timestamp": self.timestamp.isoformat()}

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "Message":
    """Create a Message from a dictionary."""
    return cls(role=data["role"], content=data["content"], timestamp=datetime.fromisoformat(data["timestamp"]))


@dataclass
class Conversation:
  """Represents a conversation with multiple messages."""

  id: str
  title: str | None = None
  messages: list[Message] = field(default_factory=list)
  created_at: datetime | None = None
  updated_at: datetime | None = None
  metadata: dict[str, Any] = field(default_factory=dict)

  def __post_init__(self) -> None:
    if self.created_at is None:
      self.created_at = datetime.now()
    if self.updated_at is None:
      self.updated_at = self.created_at

  def add_message(self, role: str, content: str) -> Message:
    """Add a new message to the conversation."""
    message = Message(role=role, content=content)
    self.messages.append(message)
    self.updated_at = datetime.now()
    return message

  def remove_message_at_index(self, index: int) -> bool:
    """Remove a message at a specific index.

    Args:
        index: Zero-based index of the message to remove

    Returns:
        True if successful, False if index is invalid
    """
    if 0 <= index < len(self.messages):
      del self.messages[index]
      self.updated_at = datetime.now()
      return True
    return False

  def remove_message_pair(self, user_index: int) -> bool:
    """Remove a user-assistant message pair.

    This assumes conversations follow the typical pattern of user message
    followed by assistant message. System messages are preserved.

    Args:
        user_index: Index of user message in the message list

    Returns:
        True if both messages were successfully removed,
        False if indices are invalid or messages don't form a pair
    """
    # Validate that the index is within range and not the last message
    # We need at least two messages (user and assistant) to remove a pair
    if not (0 <= user_index < len(self.messages) - 1):
      # Return early if index is out of range or points to the last message
      # (which can't be part of a pair since there's no next message)
      return False

    # Check that we have a user-assistant pair:
    # 1. The message at user_index must be a user message
    # 2. The following message must be an assistant message
    # This ensures we maintain conversation integrity by only removing complete exchanges
    if self.messages[user_index].role != "user" or self.messages[user_index + 1].role != "assistant":
      return False

    # We remove messages in reverse order (higher index first) to avoid
    # index shifting problems that would occur if we removed the lower index first

    # Remove the assistant message first (higher index)
    del self.messages[user_index + 1]
    # Then remove the user message
    del self.messages[user_index]

    # Update the conversation's last modified timestamp
    self.updated_at = datetime.now()
    return True

  def to_dict(self) -> dict[str, Any]:
    """Convert conversation to a dictionary for serialization."""
    return {
      "id": self.id,
      "title": self.title,
      "created_at": self.created_at.isoformat(),
      "updated_at": self.updated_at.isoformat(),
      "metadata": self.metadata,
      "messages": [msg.to_dict() for msg in self.messages],
    }

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "Conversation":
    """Create a Conversation from a dictionary."""
    conv = cls(
      id=data["id"],
      title=data.get("title"),
      created_at=datetime.fromisoformat(data["created_at"]),
      updated_at=datetime.fromisoformat(data["updated_at"]),
      metadata=data.get("metadata", {}),
    )

    for msg_data in data["messages"]:
      conv.messages.append(Message.from_dict(msg_data))

    return conv

  def get_messages_for_llm(self, include_system: bool = True) -> list[dict[str, str]]:
    """Get messages formatted for LLM API calls."""
    result = []
    for msg in self.messages:
      if not include_system and msg.role == "system":
        continue
      result.append({"role": msg.role, "content": msg.content})
    return result

  def extract_message_history(self, max_messages: int | None = None) -> str:
    """Extract message history as a formatted string for display."""
    history = []
    messages_to_include = self.messages

    if max_messages is not None and max_messages < len(messages_to_include):
      messages_to_include = messages_to_include[-max_messages:]

    for msg in messages_to_include:
      if msg.role != "system":  # Skip system messages in history display
        history.append(f"{msg.role.capitalize()}: {msg.content}")

    return "\n\n".join(history)

  def to_markdown(self) -> str:
    """Export conversation as markdown format."""
    md_content = []

    # Add conversation metadata header
    md_content.append(f"# {self.title or 'Untitled Conversation'}")
    md_content.append(f"*Conversation ID: `{self.id}`*")
    md_content.append(f"*Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}*")
    md_content.append(f"*Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')}*")

    # Add metadata section
    if self.metadata:
      md_content.append("\n## Metadata")
      for key, value in self.metadata.items():
        if value is not None:  # Only include non-None values
          md_content.append(f"- **{key}**: {value}")

    # Add conversation content
    md_content.append("\n## Conversation")

    for msg in self.messages:
      if msg.role == "system":
        # Include system messages in a collapsible details section
        md_content.append("\n<details>")
        md_content.append("<summary>System Prompt</summary>\n")
        md_content.append("```")
        md_content.append(msg.content)
        md_content.append("```")
        md_content.append("</details>\n")
      else:
        # Get non-system messages
        non_system_msgs = [m for m in self.messages if m.role != "system"]

        # Find index of this message in non-system messages
        try:
          idx = non_system_msgs.index(msg)
          # Add separator before every message except the first non-system message
          if idx > 0:
            md_content.append("\n---\n")
        except ValueError:
          # This shouldn't happen, but just in case
          pass

        # Format user and assistant messages
        md_content.append(f"### {msg.role.capitalize()}")
        md_content.append(f"*{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*\n")
        md_content.append(msg.content)

    return "\n".join(md_content)


class ConversationManager:
  """Manages conversation storage, retrieval, and manipulation."""

  def __init__(self, storage_dir: str | None = None) -> None:
    """Initialize the conversation manager with a storage directory."""
    if storage_dir is None:
      storage_dir = Path.home() / ".config" / "dejavu2-cli" / "conversations"

    self.storage_dir = Path(storage_dir)
    self.storage_dir.mkdir(parents=True, exist_ok=True)
    self.active_conversation: Conversation | None = None

    logger.debug(f"Conversation storage directory: {self.storage_dir}")

  def new_conversation(self, system_prompt: str | None = None, title: str | None = None, metadata: dict[str, Any] | None = None) -> Conversation:
    """Create a new conversation.

    Args:
      system_prompt: Initial system prompt for the conversation
      title: Optional title for the conversation
      metadata: Optional dictionary of metadata (model, temperature, etc.)

    Returns:
      A newly created Conversation object
    """
    conv_id = str(uuid.uuid4())

    # Initialize metadata if not provided
    if metadata is None:
      metadata = {}

    conv = Conversation(id=conv_id, title=title, metadata=metadata)

    # Add system message if provided
    if system_prompt:
      conv.add_message("system", system_prompt)

    self.active_conversation = conv
    logger.debug(f"Created new conversation: {conv_id}")
    return conv

  def load_conversation(self, conv_id: str) -> Conversation:
    """Load a conversation from storage by ID."""
    conv_path = self.storage_dir / f"{conv_id}.json"
    if not conv_path.exists():
      error_msg = f"Conversation not found: {conv_id}"
      logger.error(error_msg)
      raise ConversationError(error_msg)

    try:
      with open(conv_path, encoding="utf-8") as f:
        data = json.load(f)
    except OSError as e:
      error_msg = f"Error reading conversation file {conv_id}: {str(e)}"
      logger.error(error_msg)
      raise ConversationError(error_msg) from e
    except json.JSONDecodeError as e:
      error_msg = f"Invalid JSON in conversation file {conv_id}: {str(e)}"
      logger.error(error_msg)
      raise ConversationError(error_msg) from e

    try:
      # Sanitize message content to ensure they're strings
      if "messages" in data:
        for msg_data in data["messages"]:
          if "content" in msg_data and not isinstance(msg_data["content"], str):
            # Convert non-string content to string
            if hasattr(msg_data["content"], "text"):
              msg_data["content"] = msg_data["content"].text
            elif isinstance(msg_data["content"], list | dict):
              msg_data["content"] = str(msg_data["content"])
            else:
              msg_data["content"] = str(msg_data["content"])

      conv = Conversation.from_dict(data)
      self.active_conversation = conv
      logger.debug(f"Loaded conversation: {conv_id}")
      return conv
    except (KeyError, ValueError, TypeError) as e:
      error_msg = f"Invalid conversation data format in {conv_id}: {str(e)}"
      logger.error(error_msg)
      raise ConversationError(error_msg) from e

  def save_conversation(self, conv: Conversation | None = None) -> None:
    """Save a conversation to storage."""
    if conv is None:
      conv = self.active_conversation

    if conv is None:
      error_msg = "No conversation to save"
      logger.error(error_msg)
      raise ConversationError(error_msg)

    try:
      # Serialize and save with file locking
      conv_path = self.storage_dir / f"{conv.id}.json"
      with open(conv_path, "w", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        try:
          json.dump(conv.to_dict(), f, indent=2, ensure_ascii=False)
        finally:
          fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock

      logger.debug(f"Saved conversation: {conv.id}")
    except BlockingIOError as e:
      error_msg = f"Conversation file locked by another process {conv.id}: {str(e)}"
      logger.error(error_msg)
      raise ConversationError(error_msg) from e
    except OSError as e:
      error_msg = f"Error writing conversation file {conv.id}: {str(e)}"
      logger.error(error_msg)
      raise ConversationError(error_msg) from e
    except (TypeError, ValueError) as e:
      error_msg = f"Error serializing conversation {conv.id}: {str(e)}"
      logger.error(error_msg)
      raise ConversationError(error_msg) from e

  def list_conversations(self) -> list[dict[str, Any]]:
    """List all stored conversations with metadata."""
    conversations = []

    for file_path in sorted(self.storage_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
      try:
        with open(file_path, encoding="utf-8") as f:
          data = json.load(f)

        summary = {
          "id": data["id"],
          "title": data.get("title", "Untitled Conversation"),
          "message_count": len(data["messages"]),
          "created_at": data["created_at"],
          "updated_at": data["updated_at"],
        }
        conversations.append(summary)
      except (OSError, json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Error loading conversation from {file_path}: {str(e)}")
        continue

    return conversations

  def delete_conversation(self, conv_id: str) -> None:
    """Delete a conversation by ID."""
    conv_path = self.storage_dir / f"{conv_id}.json"
    if not conv_path.exists():
      error_msg = f"Conversation not found for deletion: {conv_id}"
      logger.error(error_msg)
      raise ConversationError(error_msg)

    try:
      conv_path.unlink()

      if self.active_conversation and self.active_conversation.id == conv_id:
        self.active_conversation = None

      logger.debug(f"Deleted conversation: {conv_id}")
    except OSError as e:
      error_msg = f"Error deleting conversation {conv_id}: {str(e)}"
      logger.error(error_msg)
      raise ConversationError(error_msg) from e

  def get_most_recent_conversation(self) -> Conversation | None:
    """Get the most recently modified conversation."""
    conversations = self.list_conversations()
    if not conversations:
      return None

    # First item is already the most recent due to sorting in list_conversations
    most_recent_id = conversations[0]["id"]
    return self.load_conversation(most_recent_id)

  def export_conversation_to_markdown(self, conv_id: str | None = None, output_path: str | None = None) -> str:
    """
    Export a conversation to markdown format.

    Args:
      conv_id: ID of the conversation to export. If None, uses active conversation.
      output_path: Path to save the markdown file. If None, returns the markdown content.

    Returns:
      Path to saved file if output_path is provided, otherwise the markdown content.
    """
    # Get the conversation to export
    conversation = None
    conversation = self.load_conversation(conv_id) if conv_id else self.active_conversation

    if not conversation:
      error_msg = "No conversation to export"
      logger.error(error_msg)
      raise ConversationError(error_msg)

    # Generate markdown content
    md_content = conversation.to_markdown()

    # Save to file if path is provided
    if output_path:
      try:
        with open(output_path, "w", encoding="utf-8") as f:
          f.write(md_content)
        return output_path
      except OSError as e:
        error_msg = f"Failed to write markdown file: {str(e)}"
        logger.error(error_msg)
        raise ConversationError(error_msg) from e

    # Otherwise just return the markdown content
    return md_content

  def remove_message_at_index(self, conv_id: str, index: int) -> None:
    """
    Remove a message at a specific index in a conversation.

    Args:
      conv_id: ID of the conversation
      index: Zero-based index of the message to remove
    """
    # Load the conversation (may raise ConversationError)
    conv = self.load_conversation(conv_id)

    # Remove the message
    if not conv.remove_message_at_index(index):
      error_msg = f"Failed to remove message at index {index} from conversation '{conv_id}' - Index may be out of range (available range: 0-{len(conv.messages) - 1})"
      logger.error(error_msg)
      raise ConversationError(error_msg)

    # Save changes
    self.save_conversation(conv)
    logger.info(f"Removed message at index {index} from conversation {conv_id}")

  def remove_message_pair(self, conv_id: str, user_index: int) -> None:
    """
    Remove a user-assistant message pair from a conversation.

    Args:
      conv_id: ID of the conversation
      user_index: Index of the user message to remove (assistant message will also be removed)
    """
    # Load the conversation (may raise ConversationError)
    conv = self.load_conversation(conv_id)

    # Remove the message pair
    if not conv.remove_message_pair(user_index):
      # Provide a helpful error message explaining why it might have failed
      message_count = len(conv.messages)
      if user_index >= message_count:
        error_msg = f"Failed to remove message pair: Index {user_index} is out of range (conversation has {message_count} messages)"
      elif user_index == message_count - 1:
        error_msg = f"Failed to remove message pair: Index {user_index} is the last message and doesn't have a following message to form a pair"
      elif conv.messages[user_index].role != "user":
        error_msg = (
          f"Failed to remove message pair: Message at index {user_index} is not a user message (it's a {conv.messages[user_index].role} message)"
        )
      elif conv.messages[user_index + 1].role != "assistant":
        error_msg = f"Failed to remove message pair: Message at index {user_index + 1} is not an assistant message (it's a {conv.messages[user_index + 1].role} message)"
      else:
        error_msg = f"Failed to remove message pair at index {user_index} from conversation {conv_id} for unknown reason"

      logger.error(error_msg)
      raise ConversationError(error_msg)

    # Save changes
    self.save_conversation(conv)
    logger.info(f"Removed message pair starting at index {user_index} from conversation {conv_id}")

  def list_conversation_messages(self, conv_id: str) -> list[dict[str, int | str | bool]]:
    """
    List all messages in a conversation with their indices.

    Provides a structured view of all messages in the conversation, including
    message role, content preview, timestamp, and a flag indicating if it's
    a system message.

    Args:
      conv_id: ID of the conversation to list messages from

    Returns:
      List of dictionaries with the following keys:
        - 'index': int - Zero-based index of the message in the conversation
        - 'role': str - Message role ('user', 'assistant', or 'system')
        - 'content_preview': str - First 50 chars of message content
        - 'timestamp': str - Formatted timestamp of when message was created
        - 'is_system': bool - Whether this is a system message

    Example:
      [
        {'index': 0, 'role': 'system', 'content_preview': 'You are a helpful...',
         'timestamp': '2025-03-01 12:00:00', 'is_system': True},
        {'index': 1, 'role': 'user', 'content_preview': 'Hello!',
         'timestamp': '2025-03-01 12:01:00', 'is_system': False}
      ]
    """
    # Load the conversation (may raise ConversationError)
    conv = self.load_conversation(conv_id)

    # Create list of messages with indices
    result = []
    for i, msg in enumerate(conv.messages):
      result.append(
        {
          "index": i,
          "role": msg.role,
          "content_preview": msg.content[:50] + ("..." if len(msg.content) > 50 else ""),
          "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
          "is_system": msg.role == "system",
        }
      )

    return result

  def suggest_title_from_content(self, conversation: Conversation, query_function: Callable[[str], str], max_length: int = 60) -> str:
    """Use the LLM to suggest a title for the conversation."""
    # Only try to generate title if we have at least one user and one assistant message
    user_msgs = [m for m in conversation.messages if m.role == "user"]
    asst_msgs = [m for m in conversation.messages if m.role == "assistant"]

    if not user_msgs or not asst_msgs:
      return "Untitled Conversation"

    # Get the first few exchanges to generate the title
    context = ""
    for i, msg in enumerate(conversation.messages):
      if msg.role != "system" and i < 4:  # Use first 4 non-system messages
        prefix = "User: " if msg.role == "user" else "Assistant: "
        # Truncate long messages
        content = msg.content[:100] + ("..." if len(msg.content) > 100 else "")
        context += f"{prefix}{content}\n\n"

    # Prepare the title generation prompt
    prompt = f"Based on this conversation excerpt, suggest a concise, descriptive title (5 words or less):\n\n{context}"

    try:
      title = query_function(prompt).strip()

      # Remove quotes if the LLM wrapped the title in them
      if (title.startswith('"') and title.endswith('"')) or (title.startswith("'") and title.endswith("'")):
        title = title[1:-1].strip()

      # Truncate if too long
      if max_length > 0 and len(title) > max_length:
        title = title[:max_length].rstrip() + "..."

      return title
    except Exception as e:
      logger.warning(f"Failed to generate title: {str(e)}")
      return "Untitled Conversation"
