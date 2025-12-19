# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

```bash
# Run the tool
./dv2-models-list                              # List all enabled models
./dv2-models-list -F "parent:equals:OpenAI"    # Filter by provider
./dv2-models-list -o table -l 10               # Table format, limit 10
./dv2-models-list -S                           # Show statistics

# Verify syntax
python3 -m py_compile dv2-models-list.py

# Install dependencies
pip install -r requirements.txt
```

## Requirements

- **Python 3.12+** (enforced at runtime)
- **PyYAML** (declared in requirements.txt)

## Architecture Overview

### Design Patterns

| Pattern | Implementation | Purpose |
|---------|---------------|---------|
| Abstract Factory | `Filter`, `ModelFormatter` base classes | Extensible filter/formatter system |
| Chain of Responsibility | `FilterChain` | Combine multiple filters with AND/OR logic |
| Strategy | `get_formatter()` | Runtime formatter selection |

### Data Flow

```
CLI args → ArgumentParser → load_models() → FilterChain.matches() → sort_models() → Formatter.format() → stdout
```

### Module Responsibilities

- **`dv2-models-list.py`**: CLI entry point, orchestration, `ModelLoadError` exception
- **`filters/`**: Filter implementations
  - `base.py`: `Filter` ABC, `FilterOperator` enum
  - `string_filters.py`: String ops + regex validation (`RegexValidationError`)
  - `numeric_filters.py`: Numeric comparisons
  - `chain.py`: `FilterChain` for combining filters
- **`formatters/`**: Output formatters (table, json, csv, yaml, tree)
- **`query_parser.py`**: Parses `field:operator:value` expressions, validates field paths
- **`model_stats.py`**: Statistics calculations
- **`presets.py`**: Predefined filter combinations

## Filter Expression Format

```
field:operator:value    # Standard format
field=value             # Shorthand for equals
token_costs.input:>=:0  # Nested field paths supported
```

Field paths are validated against: `^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$`

## Adding New Components

### New Filter Operator

1. Add enum value to `FilterOperator` in `filters/base.py`
2. Add operator mapping in `FilterChain._create_filter()` in `filters/chain.py`
3. Implement match logic in `StringFilter.matches()` or `NumericFilter.matches()`
4. Add alias in `query_parser.normalize_operator()` if needed

### New Output Formatter

1. Create class inheriting from `ModelFormatter` in `formatters/`
2. Implement `format(models, **kwargs) -> str` method
3. Add to `formatters/__init__.py` exports
4. Add to `get_formatter()` dictionary in `dv2-models-list.py`

## Security Notes

- **Regex patterns**: Validated for dangerous constructs (nested quantifiers) and length-limited to 500 chars
- **Field paths**: Validated before use in filter expressions
- **File loading**: Uses custom `ModelLoadError` exception with specific error types

## Known Limitations

- Numeric fields are hardcoded in `filters/chain.py:69` (`available`, `enabled`, `context_window`, etc.)
- No test suite exists
- No caching for repeated queries

#fin
