# DejaVu2-CLI Project Guide

## Commands & Development
- Run CLI: `./dejavu2-cli "Your query" [options]` or `./dv2 "query" [options]`
- Model selection: `./dejavu2-cli "query" -m claude-3-5-sonnet`
- List models: `./dejavu2-cli --list-models` `--list-template-names` `--status`
- Update models: 
  - Anthropic: `python Models/update_anthropic_models.py`
  - OpenAI: `python Models/update_openai_models.py`
  - Check model registry: `python Models/check_models_json.py`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `./run_tests.sh` or `python -m pytest`
- Run specific test categories: `./run_tests.sh --unit|--integration|--functional`
- Run single test: `python -m pytest tests/path/to/test_file.py::TestClass::test_function`
- Run with options: `./run_tests.sh --coverage` (coverage report) or `--verbose` (detailed output)

## Code Style
- Python: 2-space indentation, 100 char line limit, shebang `#!/usr/bin/env python3`
- Imports: Group by stdlib → third-party → local, sort alphabetically
- Types: Use typing module (Dict, List, Optional, Any, etc.)
- Naming: snake_case for variables/functions, PascalCase for classes
- Docstrings: Google style required for all public functions, modules, classes
- Error handling: Specific try/except blocks, avoid bare except
- Logging: Use logging module with appropriate levels, not print()
- Scripts must end with `#fin` on last line

## Architecture
- CLI: Click-based Python supporting multiple LLM providers (Anthropic, OpenAI, Google, Meta, local models)
- Config: YAML files (defaults.yaml), Models.json for model definitions
- Environment: `export ANTHROPIC_API_KEY="your-key"` for Claude, `export OPENAI_API_KEY="your-key"` for OpenAI
- Pytest configuration: See tests/pytest.ini for settings
- Ignore directories: .gudang/ (backups), .symlink, tmp/, temp/, .cache/

## Principles
- K.I.S.S. - "Everything should be made as simple as possible, but not simpler"
- Consistent formatting and error handling across all files
- Security first - NEVER store API keys in code or config files
- Test everything before committing

#fin