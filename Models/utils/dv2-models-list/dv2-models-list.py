#!/usr/bin/env python3
import sys
if sys.version_info < (3, 12):
  print("Error: Python 3.12+ required", file=sys.stderr)
  sys.exit(1)
"""
Enhanced model listing tool with advanced filtering and formatting capabilities.

Usage: dv2-models-list [OPTIONS]

Quick Examples:
  dv2-models-list                    # List all enabled models
  dv2-models-list -d                 # Include disabled models
  dv2-models-list -F "parent:equals:OpenAI"     # Filter by provider
  dv2-models-list -o table -l 10     # Table format, limit to 10
  dv2-models-list -S                 # Show statistics

Filtering:
  -F "field:operator:value"          # Add filter (can use multiple)
  -O                                 # Use OR logic between filters
  -N                                 # Negate all filters
  -C                                 # Case-sensitive matching
  -P preset_name                     # Use predefined filter preset

Output Formats:
  -o default|table|json|csv|yaml|tree  # Set output format
  -col model,alias,parent            # Specify table/csv columns
  -H                                 # No header in table/csv
  -g field                           # Group by field (tree format)

Sorting & Limiting:
  -s field1,field2                   # Sort by fields
  -r                                 # Reverse sort order
  -l N                               # Limit to N results

Statistics:
  -S                                 # Show overall statistics
  -b field                           # Count by field value
  -u field                           # Show unique field values

Other Options:
  -m path                            # Custom Models.json path
  -d                                 # Include disabled models

Filter Operators:
  equals, not_equals, contains, not_contains, starts_with, ends_with,
  regex, >, <, >=, <=, in, not_in

Common Fields:
  model, alias, parent, family, model_category, enabled, available,
  vision, context_window, max_output_tokens
"""

import argparse
import json
import pathlib
from typing import Any

# Import our modules
from filters import FilterChain


class ModelLoadError(Exception):
  """Raised when models file cannot be loaded."""
  pass


from formatters import CSVFormatter, JSONFormatter, ModelFormatter, TableFormatter, TreeFormatter, YAMLFormatter
from model_stats import ModelStatistics
from presets import FILTER_PRESETS
from query_parser import parse_filter_expression

# Get script directory
script_dir = pathlib.Path(__file__).resolve().parent


def create_parser() -> argparse.ArgumentParser:
  """Create argument parser with all options."""
  parser = argparse.ArgumentParser(prog="dv2-models-list", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

  # Filter options
  filter_group = parser.add_argument_group("Filtering Options")
  filter_group.add_argument(
    "-F", "--filter", action="append", dest="filters", help='Filter expression: "field:operator:value" (can specify multiple)'
  )
  filter_group.add_argument("-O", "--or", action="store_true", dest="use_or", help="Use OR logic between filters (default: AND)")
  filter_group.add_argument("-N", "--not", action="store_true", dest="negate", help="Negate all filters")
  filter_group.add_argument("--case-sensitive", "-C", action="store_true", help="Use case-sensitive string matching")
  filter_group.add_argument("-P", "--preset", choices=list(FILTER_PRESETS.keys()), help="Use a predefined filter preset")

  # Quick filter options
  quick_group = parser.add_argument_group("Quick Filter Options")
  quick_group.add_argument("-a", "--alias", help='Filter by alias (shortcut for -F "alias:equals:value")')
  quick_group.add_argument("-p", "--parent", help='Filter by parent/provider (shortcut for -F "parent:equals:value")')
  quick_group.add_argument("-c", "--model-category", help='Filter by category (shortcut for -F "model_category:equals:value")')
  quick_group.add_argument("-f", "--family", help='Filter by family (shortcut for -F "family:equals:value")')
  quick_group.add_argument("-v", "--available", type=int, help="Filter by available level <= N")
  quick_group.add_argument("-e", "--enabled", type=int, help="Filter by enabled level <= N")

  # Output format options
  format_group = parser.add_argument_group("Output Format Options")
  format_group.add_argument(
    "--format", "-o", choices=["default", "table", "json", "csv", "yaml", "tree"], default="default", help="Output format (default: simple list)"
  )
  format_group.add_argument("--columns", "-col", help="Comma-separated list of columns for table/csv output")
  format_group.add_argument("-H", "--no-header", action="store_true", help="Omit header row in table/csv output")
  format_group.add_argument("--group", "-g", help="Group results by field (for tree output)")

  # Sorting and limiting
  sort_group = parser.add_argument_group("Sorting and Limiting")
  sort_group.add_argument("--sort", "-s", help="Comma-separated fields to sort by")
  sort_group.add_argument("--reverse", "-r", action="store_true", help="Reverse sort order")
  sort_group.add_argument("--limit", "-l", type=int, help="Limit output to N results")

  # Statistics
  stats_group = parser.add_argument_group("Statistics and Analysis")
  stats_group.add_argument("-S", "--stats", action="store_true", help="Show model statistics")
  stats_group.add_argument("-b", "--count-by", help="Count models by field value")
  stats_group.add_argument("-u", "--unique", help="Show unique values for a field")

  # Other options
  parser.add_argument("-m", "--models-file", default=script_dir / "Models.json", help="Path to Models.json file")
  parser.add_argument("-d", "--include-disabled", action="store_true", help="Include models with available=0 or enabled=0")

  return parser


def load_models(json_path: pathlib.Path) -> dict[str, Any]:
  """
  Load models from JSON file.

  Args:
    json_path: Path to the Models.json file

  Returns:
    Dictionary of model name to model data

  Raises:
    ModelLoadError: If the file cannot be loaded or parsed
  """
  try:
    with open(json_path, encoding="utf-8") as f:
      return json.load(f)
  except FileNotFoundError:
    raise ModelLoadError(f"Models file not found: {json_path}") from None
  except PermissionError:
    raise ModelLoadError(f"Permission denied reading: {json_path}") from None
  except json.JSONDecodeError as e:
    raise ModelLoadError(f"Invalid JSON in {json_path}: {e.msg} at line {e.lineno}") from e
  except IsADirectoryError:
    raise ModelLoadError(f"Path is a directory, not a file: {json_path}") from None
  except OSError as e:
    raise ModelLoadError(f"Cannot read {json_path}: {e.strerror}") from e


def apply_legacy_filters(args: argparse.Namespace) -> list[tuple[str, str, str]]:
  """Convert legacy filter arguments to new filter format."""
  filters = []

  if args.alias:
    filters.append(("alias", "equals", args.alias))
  if args.parent:
    filters.append(("parent", "equals", args.parent))
  if args.model_category:
    filters.append(("model_category", "equals", args.model_category))
  if args.family:
    filters.append(("family", "equals", args.family))
  if args.available is not None:
    filters.append(("available", "<=", str(args.available)))
  if args.enabled is not None:
    filters.append(("enabled", "<=", str(args.enabled)))

  return filters


def main() -> int:
  """
  Main entry point.

  Returns:
    Exit code (0 for success, 1 for error)
  """
  parser = create_parser()
  args = parser.parse_args()

  # Load models
  try:
    models = load_models(args.models_file)
  except ModelLoadError as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1

  # Build filter chain
  filter_chain = FilterChain(use_or=args.use_or, negate=args.negate)

  # Add preset filters if specified
  if args.preset:
    preset_filters = FILTER_PRESETS.get(args.preset, [])
    for filter_expr in preset_filters:
      field, op, value = parse_filter_expression(filter_expr)
      filter_chain.add_filter(field, op, value, args.case_sensitive)

  # Add explicit filters
  if args.filters:
    for filter_expr in args.filters:
      field, op, value = parse_filter_expression(filter_expr)
      filter_chain.add_filter(field, op, value, args.case_sensitive)

  # Add legacy filters (with deprecation warning)
  legacy_filters = apply_legacy_filters(args)
  if legacy_filters:
    print("Warning: Legacy filter options are deprecated. Use -F instead.", file=sys.stderr)
    for field, op, value in legacy_filters:
      filter_chain.add_filter(field, op, value, args.case_sensitive)

  # Apply filters
  filtered_models = {}
  for name, data in models.items():
    # Skip disabled models unless requested
    if not args.include_disabled and (data.get("available", 0) == 0 or data.get("enabled", 0) == 0):
      continue

    if filter_chain.matches(data):
      filtered_models[name] = data

  # Handle statistics requests
  if args.stats:
    stats = ModelStatistics(filtered_models)
    stats.print_summary()
    return 0

  if args.count_by:
    stats = ModelStatistics(filtered_models)
    stats.print_count_by(args.count_by)
    return 0

  if args.unique:
    stats = ModelStatistics(filtered_models)
    stats.print_unique_values(args.unique)
    return 0

  # Sort models if requested
  if args.sort:
    sort_fields = [f.strip() for f in args.sort.split(",")]
    filtered_models = sort_models(filtered_models, sort_fields, args.reverse)

  # Apply limit if specified
  if args.limit:
    model_items = list(filtered_models.items())[: args.limit]
    filtered_models = dict(model_items)

  # Format and display output
  formatter = get_formatter(args.format)
  columns = args.columns.split(",") if args.columns else None

  output = formatter.format(filtered_models, columns=columns, show_header=not args.no_header, group_by=args.group)

  print(output)
  return 0


def sort_models(models: dict[str, Any], sort_fields: list[str], reverse: bool = False) -> dict[str, Any]:
  """Sort models by specified fields."""

  def sort_key(item: tuple[str, dict[str, Any]]) -> list[Any]:
    name, data = item
    keys = []
    for field in sort_fields:
      if field == "model":
        keys.append(name)
      else:
        value = data.get(field, "")
        # Handle None values
        if value is None:
          value = ""
        keys.append(value)
    return keys

  sorted_items = sorted(models.items(), key=sort_key, reverse=reverse)
  return dict(sorted_items)


def get_formatter(format_name: str) -> ModelFormatter:
  """Get the appropriate formatter based on format name."""
  formatters = {
    "default": TableFormatter(mode="simple"),
    "table": TableFormatter(mode="full"),
    "json": JSONFormatter(),
    "csv": CSVFormatter(),
    "yaml": YAMLFormatter(),
    "tree": TreeFormatter(),
  }
  return formatters.get(format_name, formatters["default"])


if __name__ == "__main__":
  sys.exit(main())
# fin
