"""
Table formatter for displaying models in tabular format.
"""

from typing import Any

from .base import ModelFormatter


class TableFormatter(ModelFormatter):
  """Format models as a text table."""

  def __init__(self, mode: str = "full"):
    self.mode = mode  # 'simple' or 'full'

  def format(self, models: dict[str, Any], columns: list[str] | None = None, show_header: bool = True, **kwargs) -> str:
    """Format models as a table."""
    if not models:
      return "No models found."

    if self.mode == "simple":
      # Simple format: just model (alias)
      lines = []
      for name in sorted(models.keys()):
        alias = models[name].get("alias", "")
        if alias:
          lines.append(f"{name} ({alias})")
        else:
          lines.append(name)
      return "\n".join(lines)

    # Full table mode
    if not columns:
      columns = self.get_default_columns()

    # Prepare data rows
    rows = []
    for name in sorted(models.keys()):
      row_data = self.prepare_model_data(name, models[name], columns)
      rows.append(row_data)

    # Calculate column widths
    col_widths = {}
    for col in columns:
      # Header width
      col_widths[col] = len(col)
      # Data widths
      for row in rows:
        value = str(row.get(col, ""))
        col_widths[col] = max(col_widths[col], len(value))

    # Build output
    lines = []

    # Header
    if show_header:
      header_parts = []
      separator_parts = []
      for col in columns:
        header_parts.append(col.ljust(col_widths[col]))
        separator_parts.append("-" * col_widths[col])

      lines.append(" | ".join(header_parts))
      lines.append("-+-".join(separator_parts))

    # Data rows
    for row in rows:
      row_parts = []
      for col in columns:
        value = str(row.get(col, ""))
        # Right-align numeric columns
        if col in ["available", "enabled", "context_window", "max_output_tokens", "vision"]:
          row_parts.append(value.rjust(col_widths[col]))
        else:
          row_parts.append(value.ljust(col_widths[col]))

      lines.append(" | ".join(row_parts))

    return "\n".join(lines)


# fin
