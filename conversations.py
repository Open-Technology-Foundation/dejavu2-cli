#!/usr/bin/env python3
"""
Conversation management module for dejavu2-cli.

This module handles the storage, retrieval, and manipulation of conversation
history for maintaining context across multiple queries.
"""
import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any

# Configure module logger
logger = logging.getLogger(__name__)

@dataclass
class Message:
  """Represents a single message in a conversation."""
  role: str  # "user", "assistant", or "system"
  content: str
  timestamp: datetime = None
  
  def __post_init__(self):
    if self.timestamp is None:
      self.timestamp = datetime.now()
  
  def to_dict(self) -> Dict[str, Any]:
    """Convert message to a dictionary for serialization."""
    return {
      'role': self.role,
      'content': self.content,
      'timestamp': self.timestamp.isoformat()
    }
  
  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> 'Message':
    """Create a Message from a dictionary."""
    return cls(
      role=data['role'],
      content=data['content'],
      timestamp=datetime.fromisoformat(data['timestamp'])
    )


@dataclass
class Conversation:
  """Represents a conversation with multiple messages."""
  id: str
  title: Optional[str] = None
  messages: List[Message] = field(default_factory=list)
  created_at: datetime = None
  updated_at: datetime = None
  metadata: Dict[str, Any] = field(default_factory=dict)
  
  def __post_init__(self):
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
  
  def to_dict(self) -> Dict[str, Any]:
    """Convert conversation to a dictionary for serialization."""
    return {
      'id': self.id,
      'title': self.title,
      'created_at': self.created_at.isoformat(),
      'updated_at': self.updated_at.isoformat(),
      'metadata': self.metadata,
      'messages': [msg.to_dict() for msg in self.messages]
    }
  
  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
    """Create a Conversation from a dictionary."""
    conv = cls(
      id=data['id'],
      title=data.get('title'),
      created_at=datetime.fromisoformat(data['created_at']),
      updated_at=datetime.fromisoformat(data['updated_at']),
      metadata=data.get('metadata', {})
    )
    
    for msg_data in data['messages']:
      conv.messages.append(Message.from_dict(msg_data))
    
    return conv
  
  def get_messages_for_llm(self, include_system: bool = True) -> List[Dict[str, str]]:
    """Get messages formatted for LLM API calls."""
    result = []
    for msg in self.messages:
      if not include_system and msg.role == "system":
        continue
      result.append({"role": msg.role, "content": msg.content})
    return result
  
  def extract_message_history(self, max_messages: int = None) -> str:
    """Extract message history as a formatted string for display."""
    history = []
    messages_to_include = self.messages
    
    if max_messages is not None and max_messages < len(messages_to_include):
      messages_to_include = messages_to_include[-max_messages:]
    
    for msg in messages_to_include:
      if msg.role != "system":  # Skip system messages in history display
        history.append(f"{msg.role.capitalize()}: {msg.content}")
    
    return "\n\n".join(history)


class ConversationManager:
  """Manages conversation storage, retrieval, and manipulation."""
  
  def __init__(self, storage_dir: str = None):
    """Initialize the conversation manager with a storage directory."""
    if storage_dir is None:
      home = os.path.expanduser("~")
      storage_dir = os.path.join(home, ".config", "dejavu2-cli", "conversations")
    
    self.storage_dir = Path(storage_dir)
    self.storage_dir.mkdir(parents=True, exist_ok=True)
    self.active_conversation: Optional[Conversation] = None
    
    logger.debug(f"Conversation storage directory: {self.storage_dir}")
  
  def new_conversation(self, system_prompt: str = None, title: str = None, metadata: Dict[str, Any] = None) -> Conversation:
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
  
  def load_conversation(self, conv_id: str) -> Optional[Conversation]:
    """Load a conversation from storage by ID."""
    conv_path = self.storage_dir / f"{conv_id}.json"
    if not conv_path.exists():
      logger.warning(f"Conversation not found: {conv_id}")
      return None
    
    try:
      with open(conv_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
      
      conv = Conversation.from_dict(data)
      self.active_conversation = conv
      logger.debug(f"Loaded conversation: {conv_id}")
      return conv
    except Exception as e:
      logger.error(f"Error loading conversation {conv_id}: {str(e)}")
      return None
  
  def save_conversation(self, conv: Optional[Conversation] = None) -> bool:
    """Save a conversation to storage."""
    if conv is None:
      conv = self.active_conversation
    
    if conv is None:
      logger.warning("No conversation to save")
      return False
    
    try:
      # Serialize and save
      conv_path = self.storage_dir / f"{conv.id}.json"
      with open(conv_path, 'w', encoding='utf-8') as f:
        json.dump(conv.to_dict(), f, indent=2, ensure_ascii=False)
      
      logger.debug(f"Saved conversation: {conv.id}")
      return True
    except Exception as e:
      logger.error(f"Error saving conversation {conv.id}: {str(e)}")
      return False
  
  def list_conversations(self) -> List[Dict[str, Any]]:
    """List all stored conversations with metadata."""
    conversations = []
    
    for file_path in sorted(self.storage_dir.glob("*.json"), 
                           key=os.path.getmtime, reverse=True):
      try:
        with open(file_path, 'r', encoding='utf-8') as f:
          data = json.load(f)
        
        summary = {
          'id': data['id'],
          'title': data.get('title', 'Untitled Conversation'),
          'message_count': len(data['messages']),
          'created_at': data['created_at'],
          'updated_at': data['updated_at']
        }
        conversations.append(summary)
      except Exception as e:
        logger.warning(f"Error loading conversation from {file_path}: {str(e)}")
    
    return conversations
  
  def delete_conversation(self, conv_id: str) -> bool:
    """Delete a conversation by ID."""
    conv_path = self.storage_dir / f"{conv_id}.json"
    if not conv_path.exists():
      logger.warning(f"Conversation not found for deletion: {conv_id}")
      return False
    
    try:
      conv_path.unlink()
      
      if self.active_conversation and self.active_conversation.id == conv_id:
        self.active_conversation = None
      
      logger.debug(f"Deleted conversation: {conv_id}")
      return True
    except Exception as e:
      logger.error(f"Error deleting conversation {conv_id}: {str(e)}")
      return False
  
  def get_most_recent_conversation(self) -> Optional[Conversation]:
    """Get the most recently modified conversation."""
    conversations = self.list_conversations()
    if not conversations:
      return None
    
    # First item is already the most recent due to sorting in list_conversations
    most_recent_id = conversations[0]['id']
    return self.load_conversation(most_recent_id)
  
  def suggest_title_from_content(self, conversation: Conversation, 
                              query_function: callable, 
                              max_length: int = 60) -> str:
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
    prompt = (
      f"Based on this conversation excerpt, suggest a concise, descriptive title "
      f"(5 words or less):\n\n{context}"
    )
    
    try:
      title = query_function(prompt).strip()
      
      # Remove quotes if the LLM wrapped the title in them
      if (title.startswith('"') and title.endswith('"')) or \
         (title.startswith("'") and title.endswith("'")):
        title = title[1:-1].strip()
      
      # Truncate if too long
      if max_length > 0 and len(title) > max_length:
        title = title[:max_length].rstrip() + "..."
        
      return title
    except Exception as e:
      logger.warning(f"Failed to generate title: {str(e)}")
      return "Untitled Conversation"