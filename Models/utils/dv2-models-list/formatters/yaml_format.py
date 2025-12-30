"""
YAML formatter for models output.
"""

from typing import Any, override

import yaml

from .base import ModelFormatter


class YAMLFormatter(ModelFormatter):
  """Format models as YAML."""

  @override
  def format(self, models: dict[str, Any], columns: list[str] | None = None, **kwargs) -> str:
    """Format models as YAML."""
    if columns:
      # Filter to only requested columns
      filtered_models = {}
      for name, data in models.items():
        filtered_data = self.prepare_model_data(name, data, columns)
        # Remove 'model' key since it's redundant with the dict key
        if "model" in filtered_data and filtered_data["model"] == name:
          del filtered_data["model"]
        filtered_models[name] = filtered_data

      return yaml.dump(filtered_models, default_flow_style=False, sort_keys=True)
    else:
      return yaml.dump(models, default_flow_style=False, sort_keys=True)


# fin
