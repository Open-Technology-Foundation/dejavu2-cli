# DejaVu2-CLI Project Guide

## Commands
- Run: `./dejavu2-cli "Your query" [options]` or `./dv2 "query" [options]` (alias)
- Model selection: `./dejavu2-cli "query" -m claude-3-5-sonnet`
- List/inspect: `./dejavu2-cli --list-models` `--list-template-names` `--status`
- Configuration: `./dejavu2-cli --edit-templates` `--edit-defaults`
- Debug: `./dejavu2-cli --verbose` for detailed logging

## Environment
- Required: `export ANTHROPIC_API_KEY="your-key"` for Claude models
- Required: `export OPENAI_API_KEY="your-key"` for OpenAI models
- Local Ollama: No key needed, ensure Ollama server is running
- NEVER store API keys in code or config files

## Development
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `./run_tests.sh` or `python -m pytest`
- Run specific tests: `./run_tests.sh --unit|--integration|--functional`
- Run single test: `python -m pytest tests/path/to/test_file.py`
- Run with coverage: `./run_tests.sh --coverage`
- Update version: `./version_updater.py [patch|minor|major]`
- Organization: ALWAYS ignore contents of any subdirectory called `.gudang` (storage for deprecated files)

## Code Style
- Formatting: ALWAYS use 2-space indentation, 100 char line limit
- Imports: Group by stdlib → third-party → local, sort alphabetically
- Types: Use typing module (Dict, List, Optional, Any, etc.)
- Naming: snake_case for variables/functions, PascalCase for classes
- Error handling: Specific try/except blocks, avoid bare except
- Logging: Use logging module with appropriate levels, not print()
- Documentation: Docstrings for all public functions, modules, classes

## Architecture
- CLI: Click-based Python CLI supporting multiple LLM providers
- Config: YAML files (defaults.yaml, llm-Templates.yaml)
- Models: Defined in Models.json
- OS: Ubuntu/Debian only