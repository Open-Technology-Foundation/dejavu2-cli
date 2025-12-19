# dv2-models-list

A powerful command-line tool for querying, filtering, and analyzing AI models from the dejavu2-cli Models.json registry. This tool provides advanced filtering capabilities, multiple output formats, and statistical analysis features.

## Features

- **Advanced Filtering**: Filter models by any field using various operators
- **Multiple Output Formats**: Table, JSON, CSV, YAML, and Tree views
- **Statistical Analysis**: Generate insights about model distributions and capabilities
- **Flexible Queries**: Use presets, quick filters, or complex filter expressions
- **Sorting & Limiting**: Control output order and size
- **Performance**: Efficient processing of large model registries

## Installation

The tool is part of the dejavu2-cli Models utilities.

**Requirements:**
- Python 3.12+
- PyYAML

```bash
# Install dependencies
pip install -r requirements.txt

# Make the script executable (if not already)
chmod +x dv2-models-list.py

# Create symlink for convenience (optional)
ln -s dv2-models-list.py dv2-models-list
```

## Quick Start

```bash
# List all enabled models
./dv2-models-list

# Show only OpenAI models
./dv2-models-list -p OpenAI

# Show models in table format
./dv2-models-list -o table

# Get statistics about all models
./dv2-models-list -S

# Find all GPT-4 models with high availability
./dv2-models-list -F "model:contains:gpt-4" -F "available:>=:8"
```

## Usage

```
dv2-models-list [OPTIONS]
```

### Filtering Options

| Option | Description | Example |
|--------|-------------|---------|
| `-F, --filter` | Add filter expression | `-F "parent:equals:OpenAI"` |
| `-O, --or` | Use OR logic between filters | `-F "parent:equals:OpenAI" -O -F "parent:equals:Anthropic"` |
| `-N, --not` | Negate all filters | `-F "enabled:equals:0" -N` |
| `-C, --case-sensitive` | Case-sensitive matching | `-F "model:contains:GPT" -C` |
| `-P, --preset` | Use predefined filter preset | `-P production` |

### Quick Filter Options

| Option | Description | Example |
|--------|-------------|---------|
| `-a, --alias` | Filter by alias | `-a sonnet` |
| `-p, --parent` | Filter by provider | `-p Anthropic` |
| `-c, --model-category` | Filter by category | `-c LLM` |
| `-f, --family` | Filter by family | `-f claude3` |
| `-v, --available` | Filter by availability ≤ N | `-v 5` |
| `-e, --enabled` | Filter by enabled ≤ N | `-e 1` |

### Output Format Options

| Option | Description | Example |
|--------|-------------|---------|
| `-o, --format` | Output format | `-o json` |
| `-col, --columns` | Specify columns | `-col model,alias,parent` |
| `-H, --no-header` | Omit header row | `-o csv -H` |
| `-g, --group` | Group by field (tree) | `-o tree -g parent` |

### Sorting & Limiting

| Option | Description | Example |
|--------|-------------|---------|
| `-s, --sort` | Sort by fields | `-s enabled,model` |
| `-r, --reverse` | Reverse sort order | `-s context_window -r` |
| `-l, --limit` | Limit results | `-l 10` |

### Statistics & Analysis

| Option | Description | Example |
|--------|-------------|---------|
| `-S, --stats` | Show overall statistics | `-S` |
| `-b, --count-by` | Count by field | `-b parent` |
| `-u, --unique` | Show unique values | `-u model_category` |

### Other Options

| Option | Description | Example |
|--------|-------------|---------|
| `-m, --models-file` | Custom Models.json path | `-m /path/to/Models.json` |
| `-d, --include-disabled` | Include disabled models | `-d` |

## Filter Operators

The `-F` option supports various operators for different types of comparisons:

### String Operators
- `equals` (or `=`): Exact match
- `not_equals` (or `!=`): Not equal
- `contains` (or `~`): Contains substring
- `not_contains`: Doesn't contain
- `starts_with` (or `^`): Starts with
- `ends_with` (or `$`): Ends with
- `regex`: Regular expression match (max 500 chars, dangerous patterns blocked)

### Numeric Operators
- `==`, `!=`: Equal, not equal
- `<`, `<=`: Less than, less than or equal
- `>`, `>=`: Greater than, greater than or equal
- `between`: In range (e.g., `5-10`)

### Special Operators
- `in`: In list (comma-separated)
- `not_in`: Not in list
- `exists`: Field exists
- `not_exists`: Field doesn't exist

## Filter Presets

Predefined filter combinations for common queries:

| Preset | Description | Filters Applied |
|--------|-------------|-----------------|
| `production` | Production-ready models | `available:>=:8, enabled:>=:5` |
| `experimental` | Experimental models | `available:<=:3, enabled:>=:1` |
| `vision` | Vision-capable models | `vision:>=:1` |
| `llm` | Language models only | `model_category:equals:LLM` |
| `anthropic` | Anthropic models | `parent:equals:Anthropic` |
| `openai` | OpenAI models | `parent:equals:OpenAI` |
| `large-context` | 100k+ context window | `context_window:>=:100000` |

## Examples

### Basic Queries

```bash
# List all models (simple format)
./dv2-models-list

# List all models including disabled ones
./dv2-models-list -d

# Show first 5 models
./dv2-models-list -l 5
```

### Filtering Examples

```bash
# Find all Claude models
./dv2-models-list -F "model:starts_with:claude"

# Find models with large context windows
./dv2-models-list -F "context_window:>=:100000"

# Find vision-capable GPT models
./dv2-models-list -F "vision:equals:1" -F "model:contains:gpt"

# Find all models except OpenAI
./dv2-models-list -F "parent:equals:OpenAI" -N
```

### Output Formatting

```bash
# Export as JSON
./dv2-models-list -o json > models.json

# Create CSV with specific columns
./dv2-models-list -o csv -col model,alias,parent,context_window > models.csv

# Show as tree grouped by provider
./dv2-models-list -o tree -g parent

# Pretty table with custom columns
./dv2-models-list -o table -col model,alias,enabled,context_window -l 20
```

### Statistics and Analysis

```bash
# Show overall statistics
./dv2-models-list -S

# Count models by provider
./dv2-models-list -b parent

# Show all unique model categories
./dv2-models-list -u model_category

# Statistics for vision models only
./dv2-models-list -F "vision:equals:1" -S
```

### Complex Queries

```bash
# Production-ready OpenAI or Anthropic models, sorted by context window
./dv2-models-list -P production \
  -F "parent:equals:OpenAI" -O -F "parent:equals:Anthropic" \
  -s context_window -r -o table

# Find cheap models (containing $0 in costs) with good availability
./dv2-models-list -F "token_costs:contains:$0" -F "available:>=:7" \
  -col model,alias,token_costs,available

# Export enabled LLMs as YAML, excluding Google
./dv2-models-list -F "model_category:equals:LLM" \
  -F "parent:not_equals:Google" -F "enabled:>=:1" \
  -o yaml > llms.yaml
```

## Output Formats

### Default
Simple list showing model names with aliases in parentheses.

### Table
Formatted table with aligned columns. Use `-col` to specify columns.

### JSON
Valid JSON output suitable for parsing by other tools.

### CSV
Comma-separated values with optional header. Ideal for spreadsheets.

### YAML
YAML format for configuration files or further processing.

### Tree
Hierarchical tree view. Use `-g` to specify grouping field.

## Model Fields

Common fields available for filtering and display:

- `model`: Official model identifier
- `alias`: Short nickname
- `parent`: Provider (OpenAI, Anthropic, etc.)
- `model_category`: Type (LLM, image, embed, etc.)
- `family`: Model family (gpt4, claude3, etc.)
- `available`: Availability level (0-9)
- `enabled`: Enabled status (0-9)
- `vision`: Vision capability (0 or 1)
- `context_window`: Maximum input tokens
- `max_output_tokens`: Maximum output tokens
- `token_costs`: Pricing information

## Tips

1. **Use presets** for common queries instead of multiple filters
2. **Combine filters** with `-F` for precise results
3. **Export to JSON** for integration with other tools
4. **Use statistics** (`-S`) to understand the model landscape
5. **Save complex queries** as shell aliases or scripts

## Troubleshooting

### No models found
- Check if Models.json exists in the script directory
- Use `-d` to include disabled models
- Verify filter syntax (field:operator:value)

### Incorrect filtering
- Use `-C` for case-sensitive matching
- Check operator spelling (e.g., `equals` not `equal`)
- Verify field names match exactly
- Field paths must start with a letter or underscore (not numbers or special chars)

### Performance issues
- Use `-l` to limit output for large datasets
- Consider filtering before sorting
- Use specific filters instead of regex when possible

## License

Part of the dejavu2-cli project. See the main project license for details.

#fin