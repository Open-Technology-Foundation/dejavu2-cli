"""
CSV formatter for models output.
"""

import csv
import io
from typing import Any, override

from .base import ModelFormatter


class CSVFormatter(ModelFormatter):
  """Format models as CSV."""

  @override
  def format(self, models: dict[str, Any], columns: list[str] | None = None, show_header: bool = True, **kwargs) -> str:
    """Format models as CSV."""
    if not models:
      return ""

    if not columns:
      columns = self.get_default_columns()

    # Use StringIO to build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    if show_header:
      writer.writerow(columns)

    # Write data rows
    for name in sorted(models.keys()):
      row_data = self.prepare_model_data(name, models[name], columns)
      row = [row_data.get(col, "") for col in columns]
      writer.writerow(row)

    return output.getvalue().rstrip()


# fin
