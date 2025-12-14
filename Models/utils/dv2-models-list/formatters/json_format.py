"""
JSON formatter for models output.
"""

import json
from typing import Any

from .base import ModelFormatter


class JSONFormatter(ModelFormatter):
  """Format models as JSON."""

  def format(self, models: dict[str, Any], columns: list[str] | None = None, indent: int = 2, **kwargs) -> str:
    """Format models as JSON."""
    if columns:
      # Filter to only requested columns
      filtered_models = {}
      for name, data in models.items():
        filtered_data = self.prepare_model_data(name, data, columns)
        # Remove 'model' key since it's redundant with the dict key
        if "model" in filtered_data and filtered_data["model"] == name:
          del filtered_data["model"]
        filtered_models[name] = filtered_data

      return json.dumps(filtered_models, indent=indent, sort_keys=True)
    else:
      return json.dumps(models, indent=indent, sort_keys=True)


# fin
