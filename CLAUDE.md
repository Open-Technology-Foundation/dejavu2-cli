# DejaVu2-CLI Project Guide

## Commands & Development
- Run CLI: `./dejavu2-cli "Your query" [options]` or `./dv2 "query" [options]`
- Model selection: `./dejavu2-cli "query" -m claude-3-5-sonnet`
- List models: `./dejavu2-cli --list-models` `--list-template-names` `--status`
- Update models: 
  - Anthropic: `python update_anthropic_models.py`
  - OpenAI: `python update_openai_models.py`
  - Check model registry: `python check_models_json.py`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `./run_tests.sh` or `python -m pytest`
- Run single test: `python -m pytest tests/path/to/test_file.py`
- Run with coverage: `./run_tests.sh --coverage`
- Update version: `./version_updater.py [patch|minor|major]`

## Code Style
- Python: 2-space indentation, 100 char line limit, shebang `#!/usr/bin/env python3`
- Imports: Group by stdlib → third-party → local, sort alphabetically
- Types: Use typing module (Dict, List, Optional, Any, etc.)
- Naming: snake_case for variables/functions, PascalCase for classes
- Docstrings: Required for all public functions, modules, classes
- Error handling: Specific try/except blocks, avoid bare except
- Logging: Use logging module with appropriate levels, not print()
- Scripts must end with `#fin` on last line

## Architecture
- CLI: Click-based Python supporting multiple LLM providers (Anthropic, OpenAI, Google, Meta, local models)
- Config: YAML files (defaults.yaml, llm-Templates.yaml), Models.json
- Model Registry: Models.json contains model definitions with unique aliases, parameters, and capabilities
- Environment: `export ANTHROPIC_API_KEY="your-key"` for Claude, `export OPENAI_API_KEY="your-key"` for OpenAI
- Ignore directories: .gudang/ (backups), .symlink, tmp/, temp/, .cache/
- OS: Ubuntu/Debian only

## Principles
- K.I.S.S. - "Everything should be made as simple as possible, but not simpler"
- Consistent formatting and error handling across all files
- Security first - NEVER store API keys in code or config files
- Test everything before committing

#fin