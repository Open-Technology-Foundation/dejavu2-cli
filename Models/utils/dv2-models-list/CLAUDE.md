# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Running the Tool
```bash
# Basic execution
./dv2-models-list

# With filters
./dv2-models-list -F "parent:equals:OpenAI" -o table

# Show statistics
./dv2-models-list -S

# Export to JSON
./dv2-models-list -o json > models.json
```

### Development Setup
```bash
# Make script executable
chmod +x dv2-models-list.py

# Create development symlink
ln -sf dv2-models-list.py dv2-models-list

# Python 3.6+ required - check version
python3 --version
```

## Architecture Overview

### Module Organization
The codebase follows a modular architecture with clear separation of concerns:

- **Main Entry Point**: `dv2-models-list.py` - CLI interface, argument parsing, and orchestration
- **Filters Package**: `filters/` - Filter implementations with abstract base class pattern
  - `base.py`: Abstract Filter class and FilterOperator enum
  - `string_filters.py`: String comparison operations (equals, contains, regex, etc.)
  - `numeric_filters.py`: Numeric comparisons (>, <, between, etc.)
  - `chain.py`: FilterChain for combining multiple filters with AND/OR logic
- **Formatters Package**: `formatters/` - Output formatting with pluggable formatters
  - `base.py`: Abstract ModelFormatter class
  - `table.py`, `json_format.py`, `csv_format.py`, `yaml_format.py`, `tree.py`: Specific format implementations
- **Core Modules**:
  - `query_parser.py`: Parses filter expressions ("field:operator:value")
  - `model_stats.py`: Statistical analysis functionality
  - `presets.py`: Predefined filter combinations

### Key Design Patterns

1. **Abstract Factory Pattern**: Formatters and filters use abstract base classes for extensibility
2. **Chain of Responsibility**: FilterChain combines multiple filters
3. **Strategy Pattern**: Different formatters selected at runtime based on user input

### Data Flow
1. Command line args → ArgumentParser
2. Load Models.json → Dict[str, Any]
3. Parse filter expressions → Filter objects
4. Apply FilterChain → Filtered models
5. Sort/limit if requested
6. Format output → Selected formatter
7. Print results

### Filter System Architecture
- Filters are created based on operator type and field name
- Numeric fields are auto-detected (hardcoded list in `chain.py:70-74`)
- String operators fallback for failed numeric parsing
- FilterChain handles AND/OR logic and negation

## Critical Issues from Audit

### Security Vulnerabilities
1. **Regex DoS Risk**: User-supplied regex patterns in `filters/string_filters.py:54-56` are compiled without validation
2. **Path Traversal**: Models file path in `dv2-models-list.py:144-149` accepts arbitrary paths
3. **No Input Validation**: Filter expressions and field paths lack comprehensive validation

### Reliability Issues
1. **Hard Exit on Error**: `load_models()` calls `sys.exit(1)` on JSON errors - no graceful degradation
2. **Silent Failures**: Numeric conversion errors in filters fail silently without user feedback
3. **No Error Recovery**: Missing error handling throughout the codebase

### Technical Debt
1. **No Tests**: Complete absence of unit, integration, or functional tests
2. **Hardcoded Values**: Numeric field names hardcoded in `filters/chain.py:70-74`
3. **No Logging**: No logging infrastructure for debugging
4. **Missing Type Hints**: Incomplete type annotations in several modules

## Development Notes

### Adding New Filters
1. Create new filter class inheriting from `Filter` in appropriate module
2. Implement `matches()` method
3. Add operator mapping in `FilterChain._create_filter()`
4. Update `query_parser.normalize_operator()` for any aliases

### Adding New Formatters
1. Create new formatter class inheriting from `ModelFormatter`
2. Implement `format()` method
3. Add to formatter dictionary in `get_formatter()`

### Models.json Location
The script looks for Models.json in its own directory by default. Can be overridden with `-m` flag.

### Filter Expression Format
Standard format: `field:operator:value`
- Fields can be nested: `token_costs.input:equals:0`
- Values containing colons must be last (split on first 2 colons only)
- Alternative format for equals: `field=value`

### Known Limitations
- Regex patterns have no timeout protection (DoS vulnerability)
- No caching for repeated queries
- Synchronous I/O for large JSON files
- Dict → List → Dict conversion in sorting is inefficient

#fin