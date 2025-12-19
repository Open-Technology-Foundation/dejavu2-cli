"""
Model statistics and analysis functionality.
"""

from collections import Counter
from typing import Any


class ModelStatistics:
  """Calculate and display statistics about models."""

  def __init__(self, models: dict[str, Any]):
    self.models = models

  def print_summary(self) -> None:
    """Print overall statistics summary."""
    if not self.models:
      print("No models to analyze.")
      return

    print("Model Statistics Summary")
    print("========================")
    print(f"Total models: {len(self.models)}")
    print()

    # Count by parent
    parents = Counter(m.get("parent", "Unknown") for m in self.models.values())
    print("By Provider:")
    for parent, count in parents.most_common():
      print(f"  {parent}: {count}")
    print()

    # Count by category
    categories = Counter(m.get("model_category", "Unknown") for m in self.models.values())
    print("By Category:")
    for category, count in categories.most_common():
      print(f"  {category}: {count}")
    print()

    # Availability stats
    available_counts = Counter(m.get("available", 0) for m in self.models.values())
    print("By Availability Level:")
    for level in sorted(available_counts.keys()):
      count = available_counts[level]
      print(f"  Level {level}: {count} models")
    print()

    # Enabled stats
    enabled_counts = Counter(m.get("enabled", 0) for m in self.models.values())
    print("By Enabled Level:")
    for level in sorted(enabled_counts.keys()):
      count = enabled_counts[level]
      print(f"  Level {level}: {count} models")
    print()

    # Vision capability
    vision_count = sum(1 for m in self.models.values() if m.get("vision", 0) > 0)
    print(f"Vision-capable models: {vision_count} ({vision_count / len(self.models) * 100:.1f}%)")

    # Context window stats
    context_windows = [m.get("context_window", 0) for m in self.models.values() if m.get("context_window")]
    if context_windows:
      print()
      print("Context Window Stats:")
      print(f"  Min: {min(context_windows):,} tokens")
      print(f"  Max: {max(context_windows):,} tokens")
      print(f"  Average: {sum(context_windows) / len(context_windows):,.0f} tokens")

  def print_count_by(self, field: str) -> None:
    """Print counts grouped by specified field."""
    if not self.models:
      print("No models to analyze.")
      return

    # Count values
    counts = Counter()
    for model_data in self.models.values():
      value = model_data.get(field, "[None]")
      if value is None or value == "":
        value = "[None]"
      counts[str(value)] += 1

    # Display results
    print(f"Model count by '{field}':")
    print(f"{'=' * 40}")

    # Sort by count (descending) then by value
    for value, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
      print(f"{value:30} : {count:4d}")

    print(f"{'=' * 40}")
    print(f"Total: {len(self.models)} models in {len(counts)} groups")

  def print_unique_values(self, field: str) -> None:
    """Print unique values for a field."""
    if not self.models:
      print("No models to analyze.")
      return

    # Collect unique values
    values = set()
    for model_data in self.models.values():
      value = model_data.get(field)
      if value is not None and value != "":
        values.add(str(value))

    # Display results
    print(f"Unique values for '{field}':")
    print(f"{'=' * 40}")

    if not values:
      print("[No values found]")
    else:
      for value in sorted(values):
        print(f"  {value}")

    print(f"{'=' * 40}")
    print(f"Total: {len(values)} unique values")

  def get_field_statistics(self, field: str) -> dict[str, Any]:
    """Get detailed statistics for a numeric field."""
    values = []
    for model_data in self.models.values():
      value = model_data.get(field)
      if value is not None and isinstance(value, int | float):
        values.append(value)

    if not values:
      return {}

    return {
      "count": len(values),
      "min": min(values),
      "max": max(values),
      "avg": sum(values) / len(values),
      "sum": sum(values),
      "unique": len(set(values)),
    }


# fin
