#!/usr/bin/env python3
"""
dejavu2-cli: Command-Line Interface for Interacting with Language Models

Description:
------------
`dejavu2-cli` is a powerful command-line tool that allows users to interact with various Large Language Models (LLMs) through one-shot queries. It supports models from OpenAI, Anthropic, and local LLaMA-based models via the Ollama server. The tool provides a flexible interface to customize queries, manage contexts, and utilize templates for consistent interactions.

Key Features:
-------------
- **Multi-Model Support**: Seamlessly switch between different LLMs such as GPT-4, Claude variants, and LLaMA models by specifying the model name or using predefined shortcuts.
- **Customizable Parameters**: Fine-tune responses by adjusting parameters like temperature, maximum tokens, and system prompts directly from the command line.
- **Contextual Inputs**: Enhance queries by including content from reference text files or knowledge bases, allowing for richer and more informed responses.
- **Template Management**: Utilize user-defined templates in YAML format to initialize query parameters, ensuring consistency and saving time on repetitive tasks.
- **Configuration Loading**: Automatically load default settings and user-specific configurations from YAML files, with the ability to override them via command-line options.
- **Listing and Editing Tools**: List available models, templates, and knowledge bases. Edit configuration and template files directly from the command line using your preferred text editor.
- **Status Display**: Preview the current state of all arguments and options before executing a query to verify and adjust settings as needed.

Usage:
------
Run `dejavu2-cli` with your query and desired options:

```bash
dejavu2-cli "Your query here" [options]
```

Options can be viewed using:

```bash
dejavu2-cli --help
```

Command-Line Options:
---------------------
- `-s, --systemprompt TEXT`
  Set the system prompt for the AI assistant (e.g., "You are a helpful assistant.").

- `-m, --model TEXT`
  Specify the LLM model to use (e.g., "gpt-4", "claude-2", "llama3.1").

- `-t, --temperature FLOAT`
  Set the sampling temperature for the LLM (e.g., `0.7`); higher values make output more random.

- `-M, --max-tokens INTEGER`
  Define the maximum number of tokens for the LLM to generate.

- `-r, --reference TEXT`
  Include content from reference text files as context (comma-separated list of file paths).

- `-k, --knowledgebase TEXT`
  Specify a knowledge base to query for additional context.

- `-Q, --knowledgebase-query TEXT`
  Define a query to send to the knowledge base (defaults to the main query if not provided).

- `-K, --list-knowledge-bases`
  List all available knowledge bases.

- `-T, --template TEXT`
  Use a template to initialize arguments (defined in `llm-Templates.yaml`).

- `-l, --list-template TEXT`
  List details of all templates or a specific template.

- `-L, --list-template-names`
  List the names of all available templates.

- `-E, --edit-templates`
  Edit the `llm-Templates.yaml` file using the default editor.

- `-D, --edit-defaults`
  Edit the `defaults.yaml` configuration file.

- `-S, --status`
  Display the current state of all arguments and options.

- `--list-models`
  List all available LLM models as defined in `defaults.yaml`.

Dependencies:
-------------
- **Python Version**: 3.8 or higher

- **Required Packages** (specified in `requirements.txt`):
  google.generativeai
  anthropic
  click
  openai
  PyYAML
  tzlocal


Configuration Files:
--------------------
- **defaults.yaml**: Contains default settings, model shortcuts, paths, API keys, and logging configurations.
- **llm-Templates.yaml**: Defines templates for initializing query parameters.

Templates:
----------
Templates allow you to predefine sets of parameters for common tasks. They are stored in `llm-Templates.yaml` and can include settings like the system prompt, model, temperature, and more.

Example Template Definition:
```yaml
Helpful AI:
  systemprompt: You are a friendly and helpful AI Assistant.
  model: sonnet
  max_tokens: 4000
  temperature: 0.55
  knowledgebase: ""
```

Usage:
```bash
dejavu2-cli "Explain quantum computing in simple terms." -T "Dejavu2"
```

Examples:
---------
- **Basic Query**:
  ```bash
  dejavu2-cli "What is the capital of France?"
  ```

- **Using a Template**:
  ```bash
  dejavu2-cli "Provide a summary of the latest news." -T "Summarize"
  ```

- **Specifying a Model and Adjusting Temperature**:
  ```bash
  dejavu2-cli "Generate a creative story about a flying car." -m gpt4 -t 0.9
  ```

- **Including Reference Files**:
  ```bash
  dejavu2-cli "Analyze the following code." -r "script.py,helpers.py"
  ```

- **Querying with a Knowledge Base**:
  ```bash
  dejavu2-cli "Explain the company's financial position." -k "financial_reports"
  ```

Author Information:
-------------------
- **Name**: Leet
- **Role**: Elite Full-Stack Programmer and Systems Engineer

Notes:
------
- Ensure that the Ollama server is running locally if you intend to use local LLaMA-based models.
- The script assumes you are operating on Ubuntu Linux.

---
"""
import sys
import os
import re
import unicodedata
import subprocess
import tempfile
import shutil
import time
import logging
import warnings
from glob import glob
from typing import Any, Dict, Optional
import xml.sax.saxutils
import click
import json
import yaml
from anthropic import Anthropic
from openai import OpenAI

# Constants --------------------------------------------------------------------

PRGDIR = os.path.dirname(os.path.realpath(__file__))
# Import version from version.py module
try:
  from version import __version__ as VERSION
except ImportError:
  VERSION = 'unknown'
  print("Warning: Could not import version.py module. Version will be set to 'unknown'.")
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
DEFAULT_CONFIG_PATH = os.path.join(PRGDIR, 'defaults.yaml')
USER_CONFIG_PATH = os.path.expanduser('~/.config/dejavu2-cli/config.yaml')
TEMPLATE_PATH = None  # Will be set after loading the config

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

model_parameters = {}

# POST SLUG ===============================================================================
translation_table = str.maketrans({
  '–': '-',
  '½': '-',
  '¼': '-',
  'ı': 'i',
  '•': 'o',
  'ł': 'l',
  '—': '-',
  '★': ' ',
  'ø': 'o',
  'Đ': 'D',
  'ð': 'd',
  'đ': 'd',
  'Ł': 'L',
  '´': '',
})
multi_char_replacements = {
  ' & ': ' and ',
  'œ': 'oe',
  '™': '-TM',
  'Œ': 'OE',
  'ß': 'ss',
  'æ': 'ae',
  'â�¹': 'Rs',
  '�': '-',
}
ps_html_entity_re = re.compile(r'&[^ \t]*;')
ps_non_alnum_re = re.compile(r'[^a-zA-Z0-9]+')
ps_quotes_re = re.compile(r"[\"'`’´]")
def post_slug(input_str: str, sep_char: str = '-',
    preserve_case: bool = False, max_len: int = 0) -> str:
  if sep_char == '': sep_char = '-'
  sep_char = sep_char[0]
  input_str = input_str.translate(translation_table)
  input_str = re.sub('|'.join(re.escape(key) for key in multi_char_replacements.keys()),
                     lambda m: multi_char_replacements[m.group(0)], input_str)
  input_str = ps_html_entity_re.sub(sep_char, input_str)
  input_str = unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode()
  input_str = ps_quotes_re.sub('', input_str)
  if not preserve_case:
    input_str = input_str.lower()
  input_str = ps_non_alnum_re.sub(sep_char, input_str).strip(sep_char)
  if max_len and len(input_str) > max_len:
    input_str = input_str[:max_len]
    last_sep_char_pos = input_str.rfind(sep_char)
    if last_sep_char_pos != -1:
      input_str = input_str[:last_sep_char_pos]
  return input_str


# LOAD CONFIG ===============================================================================
def load_config() -> Dict[str, Any]:
  """Load and return configuration from default and user YAML files."""
  config = {}
  try:
    with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f:
      config = yaml.safe_load(f) or {}
      config['config_file'] = DEFAULT_CONFIG_PATH
  except FileNotFoundError:
    logger.error(f"Default config file not found: {DEFAULT_CONFIG_PATH}")
    sys.exit(1)
  except yaml.YAMLError as e:
    logger.error(f"Error parsing default config: {e}")
    sys.exit(1)

  # Update with user configuration if it exists
  if os.path.exists(USER_CONFIG_PATH):
    try:
      with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
        user_config = yaml.safe_load(f) or {}
        config.update(user_config)
        config['config_file'] = USER_CONFIG_PATH
    except yaml.YAMLError as e:
      logger.error(f"Error parsing user config: {e}")
      sys.exit(1)

  # Validate required keys
  required_keys = ['paths', 'api_keys', 'defaults']
  for key in required_keys:
    if key not in config:
      logger.error(f"Missing required config key: {key}")
      sys.exit(1)

  # Ensure paths are correctly set
  config['paths']['prgdir'] = PRGDIR
  return config
# Load configuration
config = load_config()
TEMPLATE_PATH = os.path.join(PRGDIR, config['paths']['template_path'])
CUSTOMKB_EXECUTABLE = config['paths']['customkb']
VECTORDBS_PATH = config.get('vectordbs_path', '/var/lib/vectordbs')

from datetime import datetime
import tzlocal

def spacetime_placeholders(prompt='{{spacetime}}'):
  if '{{' not in prompt:
    return prompt
  now = datetime.now()
  date = now.strftime("%Y-%m-%d")
  time = now.strftime("%H:%M:%S")
  dow = now.strftime("%A")  # Full day name (e.g., "Monday")
  tz = tzlocal.get_localzone().key
  return (prompt
    .replace("{{date}}", date)
    .replace("{{time}}", time)
    .replace("{{tz}}", tz)
    .replace("{{dow}}", dow)
    .replace("{{spacetime}}", f"{dow} {date} {time} {tz}")
  )

# LOGGING ============================================================================
# Suppress UserWarnings from specific modules
warnings.filterwarnings("ignore", category=UserWarning, module=r"^anthropic\..*")
warnings.filterwarnings("ignore", category=UserWarning, module=r"^openai\..*")
# Set logging level to ERROR for specific loggers
logging.getLogger("anthropic").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
# Enable error-level logging for the rest of code
logging.basicConfig(level=logging.ERROR)


# QUERY ===============================================================================
# Initialize API clients
def get_api_key(config_key, env_var_name):
  """Get API key from config or environment variable"""
  api_key = config['api_keys'].get(config_key, '')
  if not api_key:  # If empty in config, try environment variable
    api_key = os.environ.get(env_var_name, '')
    if not api_key:
      logger.warning(f"No API key found for {config_key}. Check {env_var_name} environment variable.")
  return api_key

anthropic_api_key = get_api_key('anthropic', 'ANTHROPIC_API_KEY')
openai_api_key = get_api_key('openai', 'OPENAI_API_KEY')

anthropic_client = Anthropic(api_key=anthropic_api_key)
anthropic_client.beta_headers = {
  "anthropic-beta": "output-128k-2025-02-19"
}
#  "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
openai_client = OpenAI(api_key=openai_api_key)
llama_client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')

def query(query_text: str, systemprompt: str, messages:list, model: str, temperature: float, max_tokens: int) -> str:
  """Route the query to the appropriate API based on the model specified."""
  if max_tokens > model_parameters['max_output_tokens']:
    max_tokens = model_parameters['max_output_tokens']

  # time-space
  systemprompt = spacetime_placeholders(systemprompt)

  if model.startswith(('gpt', 'chatgpt', 'o1', 'o3')):
    return query_openai(query_text, systemprompt, model, temperature, max_tokens)
  elif model.startswith('claude'):
    return query_anthropic(query_text, systemprompt, model, temperature, max_tokens)
  elif model.startswith('llama') or model.startswith('nemo'):
    return query_llama(query_text, systemprompt, model, temperature, max_tokens)
  elif model.startswith('gemini'):
    return query_gemini(query_text, systemprompt, model, temperature, max_tokens)
  else:
    raise ValueError(f"Unknown model '{model}'")

# gemini -------------------------------------------------------------------------------
import google.generativeai as genai
def query_gemini(query: str, system: str, model: str, temperature, max_tokens) -> str:
  """Sends a query to a Gemini API (all text models) and returns the response."""
  try:
    gen_config = genai.types.GenerationConfig(
      temperature=temperature,
      max_output_tokens=max_tokens,
    )
    prompt = f"<system>\n{system}\n</system>\n\n{query}"
    model_obj = genai.GenerativeModel(model, generation_config=gen_config)
    response = model_obj.generate_content(prompt)
    if response and response.text:
      return response.text
    raise Exception(f"Model {model} is not supported or did not return a result.")
  except ValueError as ve:
    raise ve
  except Exception as e:
    print(f"Error querying {model}: {e}", file=sys.stderr)
    raise

def get_available_gemini_models():
  """Retrieves a list of available text-based Gemini models, excluding specified models."""
  try:
    available_models = genai.list_models()
    excluded_models = [ "models/aqa", "models/chat-bison-001", "models/text-bison-001", "models/gemini-1.0-pro-latest", "models/gemini-1.0-pro-vision-latest", "models/gemini-pro-vision", "models/gemini-1.5-pro-002" ]
    text_models = [
      model.name
      for model in available_models
      if "embedding" not in model.name and model.name not in excluded_models
    ]
    return text_models
  except Exception as e:
    print(f"Error listing models: {e}", file=sys.stderr)
    return []

# llama -------------------------------------------------------------------------------
def query_llama(query_text: str, systemprompt: str, model: str, temperature: float, max_tokens: int) -> str:
  """Send a query to a local LLaMA-based model via the Ollama server."""
  try:
    # No API key check needed for local Ollama server, but check that it's running
    response = llama_client.chat.completions.create(
      model=model,
      messages=[
        {"role": "system", "content": systemprompt},
        {"role": "user", "content": query_text}
      ],
      temperature=temperature,
      max_tokens=max_tokens
    )
    return response.choices[0].message.content

  except Exception as e:
    # Provide more helpful error message for common Ollama connection issues
    if "connection refused" in str(e).lower():
      logger.error(f"Connection to Ollama server failed. Make sure Ollama is running on localhost:11434.")
    else:
      logger.error(f"Error querying {model}: {e}")
    raise

# openai -------------------------------------------------------------------------------
def query_openai(query: str, system: str, model: str, temperature: float, max_tokens: int) -> str:
  """Send a query to the OpenAI API and return the response."""
  #logger.warning(f'Q1: {model=} {temperature=} {max_tokens=} {query=} {system=}')
  try:
    # Check if we have a valid API key
    if not openai_api_key:
      raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY environment variable.")
      
    # o1* Models
    if model.startswith(('o1', 'o3')):
      response = openai_client.chat.completions.create(
      model=model,
      messages=[
        { "role": "user", "content": system },
        { "role": "assistant", "content": "I have read and I understand this." },
        { "role": "user", "content": query }
      ],
      )
    # *gpt* Models
    else:
      response = openai_client.chat.completions.create(
      model=model,
      messages=[
        { "role": "system",  "content": system },
        { "role": "user",    "content": query }
      ],
      temperature=temperature,
      max_tokens=max_tokens,
      n=1, stop=''
      )
    return response.choices[0].message.content
  except Exception as e:
    logger.error(f"Error querying {model}: {e}")
    raise

# anthropic -------------------------------------------------------------------------------
def query_anthropic(query_text: str, systemprompt: str, model: str, temperature: float, max_tokens: int) -> str:
  """Send a query to the Anthropic API and return the response."""
  beta_headers = {
    "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
  }
  try:
    # Check if we have a valid API key
    if not anthropic_api_key:
      raise ValueError("Missing Anthropic API key. Set ANTHROPIC_API_KEY environment variable.")
      
    message = anthropic_client.messages.create(
      max_tokens=max_tokens,
      messages=[{"role": "user", "content": query_text}],
      model=model,
      system=systemprompt,
      temperature=temperature,
      extra_headers=beta_headers
    )
    return message.content[0].text
  except Exception as e:
    logger.error(f"Error querying {model}: {e}")
    raise


# CONTEXT =============================================================================
def get_reference_string(reference: str) -> str:
  """Process reference files and return their contents as a formatted string."""
  if not reference:
    return ''
  reference_string = ''
  reference_files = [file_name.strip() for file_name in reference.split(',')]
  for file_name in reference_files:
    try:
      base_name = os.path.splitext(os.path.basename(file_name))[0]
      with open(file_name, 'r', encoding='utf-8') as f:
        reference_content = f.read().strip()
        reference_content = xml.sax.saxutils.escape(reference_content)

      reference_string += f'<reference name="{base_name}">\n{reference_content}\n</reference>\n\n'
    except FileNotFoundError:
      logger.error(f"Reference file '{file_name}' not found.")
      raise
    except IOError as e:
      logger.error(f"Error reading reference file '{file_name}': {e}")
      raise
  return reference_string


def get_knowledgebase_string(knowledgebase: str, knowledgebase_query: str) -> str:
  """Retrieve and return context from the specified knowledge base as a formatted string."""
  if not knowledgebase:
    return ''
  knowledgebase = f"{knowledgebase}.cfg" if not knowledgebase.endswith('.cfg') else knowledgebase
  # Search for the knowledgebase file
  if not os.path.exists(knowledgebase):
    search_pattern = os.path.join(VECTORDBS_PATH, '**', knowledgebase)
    matches = glob(search_pattern, recursive=True)
    if matches:
      knowledgebase = matches[0]
    else:
      logger.error(f"Knowledgebase file '{knowledgebase}' not found in {VECTORDBS_PATH}")
      raise FileNotFoundError(f"Knowledgebase file '{knowledgebase}' not found")

  try:
    result = subprocess.run(
      [CUSTOMKB_EXECUTABLE, 'query', knowledgebase, knowledgebase_query, '--context'],
      capture_output=True, text=True, check=True
    )
    return f'<knowledgebase>\n{result.stdout.strip()}\n</knowledgebase>\n\n'
  except subprocess.CalledProcessError as e:
    logger.error(f"Error querying knowledgebase: {e.stderr.strip()}")
    raise
  except Exception as e:
    logger.error(f"Unexpected error querying knowledgebase: {e}")
    raise


#===============================================================================
def edit_yaml_file(filename: str):
  """Edit the specified YAML file using the system's default editor or 'p'."""
  editor = os.environ.get('EDITOR', 'p').strip()
  # Create a temporary copy of the file
  with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
    temp_path = temp_file.name
    shutil.copy2(filename, temp_path)
  while True:
    try:
      # Open the temporary file in the editor
      subprocess.run([editor, temp_path], check=True)
      # Validate the YAML
      with open(temp_path, 'r', encoding='utf-8') as f:
        yaml.safe_load(f)
      # If valid, replace the original file
      shutil.move(temp_path, filename)
      click.echo(f"{filename} edited and updated successfully.")
      break
    except subprocess.CalledProcessError:
      click.echo(f"Error: Failed to edit {filename}", err=True)
      break
    except yaml.YAMLError as e:
      click.echo(f"Error: Invalid YAML in edited file.\nDetails: {e}", err=True)
      if not click.confirm("Do you want to re-edit the file?"):
        click.echo("Changes discarded.")
        break


#===============================================================================
def list_knowledge_bases(vectordbs_path: str):
  """List all available knowledge bases in the specified directory."""
  if not os.path.isdir(vectordbs_path):
    raise ValueError(f"'{vectordbs_path}' is not a valid directory")

  knowledge_bases = set()  # Using set to automatically handle duplicates
  search_path = os.path.join(vectordbs_path, '**', '*.cfg')

  # Get all .cfg files and resolve to canonical paths
  for cfg_file in glob(search_path, recursive=True):
    canonical_path = os.path.realpath(cfg_file)  # Resolves symlinks to real path
    knowledge_bases.add(canonical_path)

  # Convert set back to sorted list
  knowledge_bases = sorted(knowledge_bases)

  if knowledge_bases:
    sorted_kb_names = sorted([os.path.splitext(os.path.basename(kb))[0]
                            for kb in knowledge_bases])
    print("Available Knowledge Bases:")
    for kb in sorted_kb_names:
      print(f"  {kb}")
  else:
    print("No knowledgebases found.")

  return list(knowledge_bases)


# TEMPLATES ===============================================================================
def normalize_key(key: str) -> str:
  """
  Normalize a key by converting to lowercase, removing spaces and underscores,
  and chopping off '-' and everything after it if present.
  """
  key = key.split('-')[0].strip()
  return key.lower().replace(' ', '').replace('_', '')

def load_template_data() -> Dict[str, Any]:
  """Load and return data from the template JSON file."""
  try:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as file:
      return json.load(file)
  except FileNotFoundError:
    click.echo("Error: Agents.json file not found.", err=True)
    sys.exit(1)
  except json.JSONDecodeError as e:
    click.echo(f"Error parsing JSON file: {e}", err=True)
    sys.exit(1)

def get_template(template_key: str) -> Optional[tuple[str, Dict[str, Any]]]:
  """Retrieve a template by its key, returning the key and its data if found."""
  normalized_key = normalize_key(template_key)
  data = load_template_data()
  for key, value in data.items():
    if normalize_key(key) == normalized_key:
      return key, value
  return None

def print_template(name: str, data: Dict[str, Any]) -> None:
  """Print the specified template's name and its details
      in a readable format."""
  print(f"Template: {name}")
  for key, value in data.items():
    if key == 'systemprompt':
      print(f'  {key}: """\n{value}\n"""')
    elif key != 'monospace':
      print(f"  {key}: {value}")
  print()

def list_template_names():
  """List the names of all templates with their details
      in a columnated format."""
  data = load_template_data()
  sorted_names = sorted(data.keys(), key=str.casefold)
  columns = [
    ('Template Name', 'name'),
    ('Model', 'model'),
    ('Temp', 'temperature'),
    ('Tokens', 'max_tokens'),
    ('Knowledge Base', 'knowledgebase')
  ]
  max_lengths = {col_name: len(col_name) for col_name, _ in columns}

  for template_name in sorted_names:
    template_data = data[template_name]
    for col_name, key in columns:
      value = template_name if key == 'name' else template_data.get(key, 'N/A')
      max_lengths[col_name] = max(max_lengths[col_name], len(str(value)))

  header = '  '.join(f"{col_name:<{max_lengths[col_name]}}" for col_name, _ in columns)
  click.echo(header)
  click.echo('-' * len(header))

  for template_name in sorted_names:
    template_data = data[template_name]
    row = []
    for col_name, key in columns:
      value = template_name if key == 'name' else template_data.get(key, 'N/A')
      row.append(f"{value:<{max_lengths[col_name]}}")
    click.echo('  '.join(row))

def list_templates(template: Optional[str] = None, names_only: bool = False) -> None:
  """List all templates or details of a specific template based on the provided argument."""
  data = load_template_data()

  if names_only:
    list_template_names()
    return

  if template and template != 'all':
    normalized_template = normalize_key(template)
    for key, value in data.items():
      if normalize_key(key) == normalized_template:
        print_template(key, value)
        return
    click.echo(f"Template '{template}' not found.", err=True)
  else:
    for template_name, template_data in data.items():
      print_template(template_name, template_data)

# LIST LLM MODELS ============================================================
def list_models(details=False) -> None:
  """List all LLM models as defined in Models.json."""
  if details:
    models = list_available_canonical_models_with_details()
    for name, details in models.items():
      click.echo(f"Model: {name}")
      for key, value in details.items():
        click.echo(f"  {key}: {value}")
      click.echo()
  else:
    models = list_available_canonical_models()
    for name in models:
      click.echo(f"{name}")
  return

def list_available_canonical_models(json_file=None):
  if not json_file:
    json_file = f"{PRGDIR}/Models.json"
  try:
    with open(json_file, 'r', encoding='utf-8') as file:
      models = json.load(file)
  except FileNotFoundError:
    click.echo(f"Error: The file '{json_file}' was not found.", err=True)
    return []
  except json.JSONDecodeError:
    click.echo(f"Error: The file '{json_file}' contains invalid JSON.", err=True)
    return []
  # Extract canonical model names where 'available' is not 0
  canonical_names = [
    name for name, details in models.items()
    if details.get('available') != 0
  ]
  # Sort the canonical model names
  canonical_names.sort()
  return canonical_names

def get_canonical_model(model_name):
  """
  Get canonical name of model, and grab model parameters
  """
  json_file = f"{PRGDIR}/Models.json"

  try:
    with open(json_file, 'r', encoding='utf-8') as file:
      models = json.load(file)
  except FileNotFoundError:
    # critical error
    click.echo(f"Error: The file '{json_file}' was not found.", err=True)
    sys.exit(1)
  except json.JSONDecodeError:
    # critical error
    click.echo(f"Error: The file '{json_file}' contains invalid JSON.", err=True)
    sys.exit(1)

  # Check if the model name is a canonical name
  canonical_name = None
  if model_name not in models:
    # Search through aliases
    for name, details in models.items():
      if details.get('alias') == model_name:
        if details.get('available') == 0:
          click.echo(f"Alias '{model_name}' was found but is unavailable", err=True)
          return None
        if details.get('enabled') == 0:
          click.echo(f"Alias '{model_name}' was found but is not enabled", err=True)
          return None
        canonical_name = name
        break
  else:
    canonical_name = model_name

  if not canonical_name:
    # Model name not found
    click.echo(f"Model '{model_name}' not found.", err=True)
    return canonical_name

  global model_parameters
  # Initialize `model_params` from Models.json
  required_fields = [
    'model',
    'series',
    'url',
    'apikey',
    'context_window',
    'max_output_tokens',
    'available',
    'enabled'
  ]
  model_info = models.get(canonical_name, {})
  for field in required_fields:
    model_parameters[field] = model_info.get(field)

  return canonical_name

def list_available_canonical_models_with_details(json_file=None):
  if not json_file:
    json_file = f"{PRGDIR}/Models.json"
  try:
    with open(json_file, 'r', encoding='utf-8') as file:
      models = json.load(file)
  except FileNotFoundError:
    click.echo(f"Error: The file '{json_file}' was not found.", err=True)
    return {}
  except json.JSONDecodeError:
    click.echo(f"Error: The file '{json_file}' contains invalid JSON.", err=True)
    return {}
  # Extract models where 'available' is greater than 0
  available_models = {
    name: details for name, details in models.items()
    if details.get('available') > 0
  }
  return available_models

def edit_models_file(filename: str):
  """Edit Models.json file using the system's default editor or 'p'."""
  editor = os.environ.get('EDITOR', 'p').strip()
  # Create a temporary copy of the file
  with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
    temp_path = temp_file.name
    shutil.copy2(filename, temp_path)
  while True:
    try:
      # Open the temporary file in the editor
      subprocess.run([editor, temp_path], check=True)
      # Validate the JSON
      with open(temp_path, 'r', encoding='utf-8') as f:
        json.load(f)
      # If valid, replace the original file
      shutil.move(temp_path, filename)
      click.echo(f"{filename} edited and updated successfully.")
      break
    except subprocess.CalledProcessError:
      click.echo(f"Error: Failed to edit {filename}", err=True)
      break
    except yaml.YAMLError as e:
      click.echo(f"Error: Invalid YAML in edited file.\nDetails: {e}", err=True)
      if not click.confirm("Do you want to re-edit the file?"):
        click.echo("Changes discarded.")
        break

# MAIN ===============================================================================
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('query_text', nargs=-1, required=False)
@click.version_option(version=VERSION, prog_name='dejavu2-cli')
@click.option('-p', '--project-name', default=None,
        help='The project name for recording conversations (eg, -p "bali_market")')

@click.option('-s', '--systemprompt', default=None,
        help='The system role for the AI assistant (eg, "You are a helpful assistant.")')
@click.option('-m', '--model', default=None,
        help='The LLM model to use (eg, "gpt-4")')
@click.option('-t', '--temperature', type=float, default=None,
        help='The sampling temperature for the LLM (eg, 0.7)')
@click.option('-M', '--max-tokens', type=int, default=None,
        help='The maximum number of tokens for the LLM (eg, 1000)')

@click.option('-r', '--reference', default=None,
        help='A comma-delimited list of text files for inclusion as context before the query')

@click.option('-k', '--knowledgebase', default=None,
        help='The knowledge base for the query (eg, "my_knowledge_base")')
@click.option('-Q', '--knowledgebase-query', default=None,
        help='Query to be sent to the knowledge base instead of the command-line query')
@click.option('-K', '--list-knowledge-bases', is_flag=True, default=False,
        help='List all available knowledge bases')

@click.option('-T', '--template', default=None,
        help='The template name to initialize arguments from (eg, "Helpful_AI")')
@click.option('-l', '--list-template', default=None,
        help='List all templates, or a specific template (eg, "all" or "Helpful_AI")')
@click.option('-L', '--list-template-names', is_flag=True, default=False,
        help='List the templates, without the systemprompt')
@click.option('-E', '--edit-templates', is_flag=True, default=False,
        help='Edit llm-Templates.yaml file')

@click.option('-D', '--edit-defaults', is_flag=True, default=False,
        help='Edit defaults.yaml file')

@click.option('-S', '--status', is_flag=True, default=False,
        help='Display the state of all arguments and exit')

@click.option('-a', '--list-models', is_flag=True, default=False,
        help='List all available models from Models.json')
@click.option('-A', '--list-models-details', is_flag=True, default=False,
        help='List all available models from Models.json, and display all elements')
@click.option('-d', '--edit-models', is_flag=True, default=False,
        help='Edit Models.json')

@click.option('-o', '--output-dir', default=None,
              help='Directory to output results to (eg, "/tmp/myfiles")')

@click.option('-g', '--message', type=(str, str), multiple=True,
        help='Add message pairs in the form: -g role "message" (eg, -g user "hello" -g assistant "hi")')

def main(**kwargs: Any) -> None:
  """
  Main entry point for the dejavu2-cli program, handling command-line arguments and executing queries.
  """
  # Handle special options first
  if kwargs['edit_templates']:
    edit_yaml_file(TEMPLATE_PATH)
    return

  if kwargs['edit_defaults']:
    edit_yaml_file(DEFAULT_CONFIG_PATH)
    return

  if kwargs['list_template']:
    list_templates(kwargs['list_template'])
    return

  if kwargs['list_template_names']:
    list_template_names()
    return

  if kwargs['list_models']:
    list_models(False)
    return
  if kwargs['list_models_details']:
    list_models(True)
    return
  if kwargs['edit_models']:
    edit_models(False)
    return

  if kwargs['list_knowledge_bases']:
    list_knowledge_bases(VECTORDBS_PATH)
    return

  if kwargs['output_dir']:
    output_dir = kwargs.get('output_dir')
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
  else:
    output_dir = ''

  # Give conversations a project name
  project_name = ''
  if kwargs['project_name']:
    project_name = post_slug(kwargs['project_name'], '-', False, 24)
  if not project_name:
    project_name = 'noproj'

  # Read query texts
  query_texts = list(kwargs.get('query_text') or [])
  if not sys.stdin.isatty():
    stdin_input = sys.stdin.read()
    if stdin_input:
      query_texts.append(stdin_input)
  if not query_texts:
    click.echo(f"Require at least one query. Use '{SCRIPT_NAME} --help' for help.", err=True)
    sys.exit(1)

  # Determine knowledgebase query
  knowledgebase_query = kwargs.get('knowledgebase_query')
  if not knowledgebase_query and query_texts:
    knowledgebase_query = query_texts[0]

  # Load defaults
  defaults = config['defaults']

  # Process template if specified
  if kwargs['template'] or defaults.get('template'):
    template_name = kwargs['template'] or defaults.get('template')
    template_data = get_template(template_name)
    if template_data:
      key, template = template_data
      kwargs['template'] = key
      for k, v in template.items():
        if k in kwargs and (kwargs[k] is None or kwargs[k] == defaults.get(k)):
          kwargs[k] = v
    else:
      click.echo(f"Template '{template_name}' not found.", err=True)
      sys.exit(1)

  messages = kwargs.get('message', [])

  # Set default values for any remaining None parameters
  for key, default_value in defaults.items():
    if kwargs.get(key) is None:
      kwargs[key] = default_value


  global model_parameters
  model_parameters = {}
  kwargs['model'] = get_canonical_model(kwargs['model'])
  if kwargs['model'] == None:
    sys.exit(1)
#  click.echo("Model Parameters:", err=True)
#  for key, value in model_parameters.items():
#    click.echo(f"  {key}: {value}", err=True)
#  click.echo(f"{model_parameters['max_output_tokens']=}")

  if kwargs['status']:
    kwargs['systemprompt'] = kwargs['systemprompt'].strip()
    if 'config_file' in config:
      click.echo(f"Config File: {config['config_file']}")
    click.echo(f"systemprompt: '''\n{kwargs['systemprompt']}\n'''")
    query_texts = [qt.strip() for qt in query_texts]
    click.echo(f"query_texts: '''\n{query_texts}\n'''")
    for key, value in kwargs.items():
      if key not in {'systemprompt', 'query_text', 'status', 'list_template', 'list_template_names', 'list_models', 'list_knowledge_bases', 'edit_defaults', 'edit_templates', 'edit_models', 'list_models_details'}:
        click.echo(f"{key}: {value if value else 'None'}")
    return

  # Process references
  try:
    reference_string = get_reference_string(kwargs['reference'])
  except Exception as e:
    click.echo(f"Error: {str(e)}", err=True)
    sys.exit(1)

  # Process knowledgebase
  if kwargs['knowledgebase']:
    try:
      knowledgebase_string = get_knowledgebase_string(kwargs['knowledgebase'], knowledgebase_query)
    except FileNotFoundError as e:
      click.echo(f"Error: {str(e)}", err=True)
      sys.exit(1)
  else:
    knowledgebase_string = ''

  # Execute queries --------------------------------------------------------
  query_result = ''
  prev_query_text = ''
  LLM_Queries = [ '', '' ]
  output_files = []
  output_order = 0
  for query_text in query_texts:
    # if multiple queries, append the result of the previous query results
    if query_result:
      query_result = f"""

<ChainOfThought>
---User:

{prev_query_text.strip()}

---Assistant:

{query_result.strip()}

</ChainOfThought>

"""


    LLM_Queries = [ '<LLM_Queries>\n', '\n</LLM_Queries>\n' ]
    # Combine all parts of the query
    full_query = f"{LLM_Queries[0]}<Query>\n{reference_string}\n{knowledgebase_string}\n{query_result}\n{query_text}\n</Query>{LLM_Queries[1]}\n"
    # Execute the query
    try:
      query_result = query(
        full_query,
        systemprompt=kwargs['systemprompt'],
        messages=messages,
        model=kwargs['model'],
        temperature=kwargs['temperature'],
        max_tokens=kwargs['max_tokens']
      )
      click.echo(query_result + '\n')
      if output_dir:
        output_order += 1
        safe_query = "".join(c for c in query_text[:100] if c.isalnum() or c in (' ', '_')).rstrip()
        safe_query = post_slug(safe_query, '-', False, 60)
        filename = os.path.join(output_dir,
            f'dv2_{project_name}_{int(time.time())}_{output_order}_{safe_query}.txt')

        with open(filename, 'w', encoding='utf-8') as file:
          file.write(f"---User:\n\n{query_text.strip()}\n\n")

        with open(filename, 'a', encoding='utf-8') as f:
          f.write(f"---Assistant:\n\n{query_result.strip()}\n\n")

        output_files.append(filename)
    except Exception as e:
      click.echo(f"Error: {str(e)}", err=True)
      sys.exit(1)
    prev_query_text = query_text

  # Write out all the files to one CoT conversation -------------------------
  if len(output_files):
    filename_cot = os.path.join(output_dir, f'dv2_{project_name}_{int(time.time())}_0_.txt')
    # Initialize the combined output file
    with open(filename_cot, 'w', encoding='utf-8') as cot_file:
      cot_file.write('')  # Ensure the file is empty before appending
    # Open the combined file once in append mode for efficiency
    with open(filename_cot, 'a', encoding='utf-8') as cot_file:
      for filename in output_files:
        # Open each output file in read mode
        with open(filename, 'r', encoding='utf-8') as file:
          # Read the entire content of the current file
          contents = file.read()
        # Append the content to the combined file with two newlines for separation
        cot_file.write(contents + '\n\n')

if __name__ == '__main__':
  main()

#fin
