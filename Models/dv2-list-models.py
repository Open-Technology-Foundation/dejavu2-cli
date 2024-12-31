#!/usr/bin/env python3
import json
import pathlib
import argparse

# Get script directory, resolving any symlinks
script_dir = pathlib.Path(__file__).resolve().parent

# Create parser with extended description including examples
description = '''
Display AI models from 'Models.json' with optional filtering.

Examples:
  # Show all models in default format
  %(prog)s

  # Show all models with full details
  %(prog)s -m long

  # Show only OpenAI models
  %(prog)s -p openai

  # Show enabled GPT-4 family models
  %(prog)s -f gpt4 -e 1

  # Show enabled OpenAI LLM models in detail
  %(prog)s -m long -p openai -c llm -e 1

  # Show models with alias 'sonnet'
  %(prog)s -a sonnet

  # Show all available models for level 9 (highest) and lower
  %(prog)s -v 9

  # Show models with available <= 1 and enabled <=9
  %(prog)s -v 1 -e 9
'''

parser = argparse.ArgumentParser(
  description=description,
  formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('-m', '--mode', choices=['default', 'short', 'long'],
  default='default',
  help='Display mode: default="name (alias)", short=name only, long=all details')
# Add filter arguments
parser.add_argument('-a', '--alias',
  help='Filter by alias (e.g., -a chatgpt)')
parser.add_argument('-p', '--parent',
  help='Filter by parent organization (e.g., -p OpenAI)')
parser.add_argument('-c', '--model-category',
  help='Filter by model category (e.g., -c LLM)')
parser.add_argument('-f', '--family',
  help='Filter by model family (e.g., -f gpt4)')
parser.add_argument('-s', '--series',
  help='Filter by model series (e.g., -s gpt4)')
parser.add_argument('-v', '--available', type=int, choices=range(10),
  help='Filter by available status <= 0-9 (e.g., -v 1)')
parser.add_argument('-e', '--enabled', type=int, choices=range(10),
  help='Filter by enabled status <= 0-9 (e.g., -e 1)')

args = parser.parse_args()
mode = args.mode

# Construct path to JSON file
json_path = script_dir / 'Models.json'

# Read the JSON file
with open(json_path, 'r', encoding='utf-8') as f:
  models = json.load(f)

# Filter models
def filter_models(models):
  return {name: data for name, data in models.items() if
          (not args.alias or
           data.get('alias', '').lower() == args.alias.lower()) and
          (not args.parent or
           data.get('parent', '').lower() == args.parent.lower()) and
          (not args.model_category or
           data.get('model_category', '').lower() == args.model_category.lower()) and
          (not args.family or
           data.get('family', '').lower() == args.family.lower()) and
          (not args.series or
           data.get('series', '').lower() == args.series.lower()) and
          (args.available is None or
           data.get('available') <= args.available) and
          (args.enabled is None or
           data.get('enabled') <= args.enabled)}

filtered_models = filter_models(models)

# Display results
if mode == 'default':
  for name in sorted(filtered_models):
    alias = filtered_models[name].get('alias', '')
    print(f"{name} ({alias})")
elif mode == 'short':
  for name in sorted(filtered_models):
    print(name)
elif mode == 'long':
  for name in sorted(filtered_models):
    print(f"\nModel: {name}")
    data = filtered_models[name]
    max_key_length = max(len(k) for k in data)
    for k, v in sorted(data.items()):
      print(f"  {k:<{max_key_length}} : {v}")

#fin
