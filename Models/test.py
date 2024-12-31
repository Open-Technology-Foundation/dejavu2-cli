import json
import sys

def get_model_name(model_name, json_file='Models.json'):
  try:
    with open(json_file, 'r') as file:
      models = json.load(file)
  except FileNotFoundError:
    print(f"Error: The file '{json_file}' was not found.", file=sys.stderr)
    sys.exit(1)
  except json.JSONDecodeError:
    print(f"Error: The file '{json_file}' contains invalid JSON.", file=sys.stderr)
    sys.exit(1)
  # Check if the model name is a canonical name
  if model_name in models:
    return model_name
  # Search through aliases
  for canonical_name, details in models.items():
    if details.get('alias') == model_name:
      return canonical_name
  # Model name not found
  return None

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("get_model_name - retrieve canonical model name from Models.json", file=sys.stderr)
    print("Usage: get_model_name <model_name>", file=sys.stderr)
    sys.exit(1)
  model_name_input = sys.argv[1].strip()
  canonical_name = get_canonical_model_name(model_name_input)
  if canonical_name:
    print(canonical_name)
  else:
    print(f"Canonical Model for '{model_name_input}' not found", file=sys.stderr)
    sys.exit(1)  # Exit with status 1 if not found
    