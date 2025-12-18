"""
Provider modules for Claude-based model updates
"""

from typing import Any


class BaseProvider:
  """Base class for provider modules"""

  @staticmethod
  def get_search_prompt() -> str:
    """Return the prompt for Claude to search for model information"""
    raise NotImplementedError("Provider must implement get_search_prompt()")

  @staticmethod
  def validate_and_format(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and format Claude's response into Models.json format

    Returns:
        Dict mapping model_id to model data in Models.json format
    """
    raise NotImplementedError("Provider must implement validate_and_format()")
