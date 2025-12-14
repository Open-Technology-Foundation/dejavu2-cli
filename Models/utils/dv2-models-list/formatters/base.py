"""
Base formatter class for output formatting.
"""

from abc import ABC, abstractmethod
from typing import Any


class ModelFormatter(ABC):
  """Abstract base class for all output formatters."""

  @abstractmethod
  def format(self, models: dict[str, Any], **kwargs) -> str:
    """
    Format the models data for output.

    Args:
      models: Dictionary of model name to model data
      **kwargs: Additional formatting options

    Returns:
      Formatted string output
    """
    pass

  def get_all_fields(self, models: dict[str, Any]) -> list[str]:
    """Get all unique fields across all models."""
    fields = set()
    for model_data in models.values():
      fields.update(model_data.keys())
    return sorted(fields)

  def get_default_columns(self) -> list[str]:
    """Get default columns for display."""
    return ["model", "alias", "parent", "model_category", "available", "enabled"]

  def prepare_model_data(self, name: str, data: dict[str, Any], columns: list[str] | None = None) -> dict[str, Any]:
    """Prepare model data for display with selected columns."""
    result = {"model": name}  # Always include model name

    if columns:
      for col in columns:
        if col == "model":
          continue  # Already added
        result[col] = data.get(col, "")
    else:
      result.update(data)

    return result


# fin
