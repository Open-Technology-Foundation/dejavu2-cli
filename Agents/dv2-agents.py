#!/usr/bin/env python3

import json
import os
import sys
import tempfile
import yaml
import argparse
import re
from typing import Dict, Any

# Add parent directory to path to import security module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security import get_editor_subprocess, validate_editor_path

DEFAULT_EDITOR = '/usr/bin/nano'

script_dir = os.path.dirname(os.path.realpath(__file__))

DEFAULT_JSON_FILE = f"{script_dir}/Agents.json"

# Default values for new agents
DEFAULT_AGENT = {
  "category": "General",
  "systemprompt": "You are a helpful AI assistant.",
  "model": "claude-3-5-sonnet-latest",
  "max_tokens": 8192,
  "temperature": 0.072973525693,
  "knowledgebase": "",
  "monospace": False
}

def validate_key(key: str) -> bool:
  """Validate key format: name - shortdesc"""
  if len(key) < 8:
    print("Error: Key must be at least 8 characters long", file=sys.stderr)
    return False

  pattern = r'^[A-Za-z0-9]+\s*-\s*.+$'
  if not re.match(pattern, key):
    print("Error: Key must follow format 'name - shortdesc' where name contains no spaces", file=sys.stderr)
    return False

  return True

def load_json(filename: str) -> Dict[str, Any]:
  try:
    with open(filename, 'r') as f:
      return json.load(f)
  except FileNotFoundError:
    print(f"Error: {filename} not found", file=sys.stderr)
    sys.exit(1)
  except json.JSONDecodeError:
    print(f"Error: {filename} is not valid JSON", file=sys.stderr)
    sys.exit(1)

def save_json(data: Dict[str, Any], filename: str):
  with open(filename, 'w') as f:
    json.dump(data, f, indent=2)

def find_key(data: Dict[str, Any], search_key: str) -> str:
  """Find full key based on case-insensitive partial match"""
  search_key = search_key.lower()
  for key in data.keys():
    parts = [p.strip().lower() for p in key.split('-')]
    if search_key in parts or search_key == key.lower():
      return key
  return None

def list_agents(data: Dict[str, Any], long: bool = False, key: str = None):
  if key:
    full_key = find_key(data, key)
    if not full_key:
      print(f"Error: Agent '{key}' not found", file=sys.stderr)
      return
    if long:
      print(f"{full_key}:")
      print(json.dumps(data[full_key], indent=2))
    else:
      print(full_key)
  else:
    if long:
      print(json.dumps(data, indent=2))
    else:
      for key in data.keys():
        print(key)

def insert_agent(data: Dict[str, Any], key: str, **kwargs):
  if not validate_key(key):
    return

  # Check for existing key (case insensitive)
  if find_key(data, key.split('-')[0].strip()):
    print(f"Error: Agent with name '{key.split('-')[0].strip()}' already exists", file=sys.stderr)
    return

  new_agent = DEFAULT_AGENT.copy()
  new_agent.update(kwargs)
  data[key] = new_agent
  save_json(data, DEFAULT_JSON_FILE)
  print(f"Added agent: {key}")

def remove_agent(data: Dict[str, Any], key: str):
  full_key = find_key(data, key)
  if not full_key:
    print(f"Error: Agent '{key}' not found", file=sys.stderr)
    return

  del data[full_key]
  save_json(data, DEFAULT_JSON_FILE)
  print(f"Removed agent: {full_key}")

def list_categories(data: Dict[str, Any]):
  """List all unique categories from Agents.json"""
  categories = set(agent["category"] for agent in data.values())
  if categories:
    print("\n".join(sorted(categories)))
  else:
    print("No categories found", file=sys.stderr)

def edit_agent(data: Dict[str, Any], key: str):
  full_key = find_key(data, key)
  if not full_key:
    print(f"Error: Agent '{key}' not found", file=sys.stderr)
    return

  # Create a copy of the data to modify
  agent_data = {full_key: data[full_key].copy()}

  # Manually format the YAML with folded style for systemprompt
  yaml_lines = []
  yaml_lines.append(f'"{full_key}":')

  for k, v in agent_data[full_key].items():
    if k == 'systemprompt':
      yaml_lines.append('  systemprompt: >')
      # Indent the systemprompt content
      for line in v.split('\n'):
        yaml_lines.append(f'    {line}')
    else:
      # Handle other fields normally
      if isinstance(v, bool):
        yaml_lines.append(f'  {k}: {str(v).lower()}')
      elif isinstance(v, (int, float)):
        yaml_lines.append(f'  {k}: {v}')
      else:
        yaml_lines.append(f'  {k}: "{v}"')

  agent_yaml = '\n'.join(yaml_lines)

  # Create temporary file
  with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as tf:
    tf.write(agent_yaml)
    temp_filename = tf.name

  # Get editor from environment or use default
  editor = os.environ.get('EDITOR', DEFAULT_EDITOR)

  # Open editor with secure subprocess
  try:
    safe_editor = validate_editor_path(editor)
    secure_subprocess = get_editor_subprocess()
    secure_subprocess.run([safe_editor, temp_filename])
  except Exception as e:
    print(f"Error opening editor: {e}", file=sys.stderr)
    os.unlink(temp_filename)
    return

  # Read modified content
  with open(temp_filename, 'r') as tf:
    modified_yaml = tf.read()

  # Clean up temp file
  os.unlink(temp_filename)

  # Parse the modified YAML
  try:
    modified_data = yaml.safe_load(modified_yaml)
    if modified_data != yaml.safe_load(agent_yaml):
      data[full_key] = modified_data[full_key]
      save_json(data, DEFAULT_JSON_FILE)
      print(f"Updated agent: {full_key}")
    else:
      print("No changes made")
  except yaml.YAMLError as e:
    print(f"Error parsing modified YAML: {e}", file=sys.stderr)
    return

def XXXedit_agent(data: Dict[str, Any], key: str):
  full_key = find_key(data, key)
  if not full_key:
    print(f"Error: Agent '{key}' not found", file=sys.stderr)
    return

  # Convert to YAML
  agent_yaml = yaml.dump({full_key: data[full_key]},
                        default_flow_style=False,
                        allow_unicode=True,
                        width=1000)

  # Create temporary file
  with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as tf:
    tf.write(agent_yaml)
    temp_filename = tf.name

  # Get editor from environment or use default
  editor = os.environ.get('EDITOR', DEFAULT_EDITOR)

  # Open editor with secure subprocess
  try:
    safe_editor = validate_editor_path(editor)
    secure_subprocess = get_editor_subprocess()
    secure_subprocess.run([safe_editor, temp_filename])
  except Exception as e:
    print(f"Error opening editor: {e}", file=sys.stderr)
    os.unlink(temp_filename)
    return

  # Read modified content
  with open(temp_filename, 'r') as tf:
    modified_yaml = tf.read()

  # Clean up temp file
  os.unlink(temp_filename)

  # If content changed, update JSON
  if yaml.safe_load(modified_yaml) != yaml.safe_load(agent_yaml):
    modified_data = yaml.safe_load(modified_yaml)
    data[full_key] = modified_data[full_key]
    save_json(data, DEFAULT_JSON_FILE)
    print(f"Updated agent: {full_key}")
  else:
    print("No changes made")

def main():
  parser = argparse.ArgumentParser(description='JSON editor for Agents.json')
  subparsers = parser.add_subparsers(dest='command')

  # List command
  list_parser = subparsers.add_parser('list')
  list_parser.add_argument('-l', '--long', action='store_true')
  list_parser.add_argument('key', nargs='?')

  # Categories command
  subparsers.add_parser('categories')

  # Insert command
  insert_parser = subparsers.add_parser('insert')
  insert_parser.add_argument('key')
  insert_parser.add_argument('--category')
  insert_parser.add_argument('--systemprompt')
  insert_parser.add_argument('--model')
  insert_parser.add_argument('--max_tokens', type=int)
  insert_parser.add_argument('--temperature', type=float)
  insert_parser.add_argument('--knowledgebase')
  insert_parser.add_argument('--monospace', type=bool)

  # Remove command
  remove_parser = subparsers.add_parser('remove')
  remove_parser.add_argument('key')

  # Edit command
  edit_parser = subparsers.add_parser('edit')
  edit_parser.add_argument('key')

  args = parser.parse_args()

  data = load_json(DEFAULT_JSON_FILE)

  if args.command == 'list':
    list_agents(data, args.long, args.key)
  elif args.command == 'categories':
    list_categories(data)
  elif args.command == 'insert':
    kwargs = {k: v for k, v in vars(args).items()
             if k not in ['command', 'key'] and v is not None}
    insert_agent(data, args.key, **kwargs)
  elif args.command == 'remove':
    remove_agent(data, args.key)
  elif args.command == 'edit':
    edit_agent(data, args.key)
  else:
    parser.print_help()

if __name__ == '__main__':
  main()
