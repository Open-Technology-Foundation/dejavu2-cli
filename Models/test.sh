#!/bin/bash
set -euo pipefail
declare -- temp=$(ls -la |sort)

# Check for exactly one argument
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <model_name>" >&2
  exit 1
fi

model_name="$1"
json_file="Models.json"

# Verify that the JSON file exists
if [ ! -f "$json_file" ]; then
  echo "Error: File '$json_file' not found." >&2
  exit 1
fi

# Attempt to find the model name as a canonical name
canonical=$(jq -r --arg name "$model_name" '
  if has($name) then
    $name
  else
    empty
  end
' "$json_file")

if [ -n "$canonical" ]; then
  echo "$canonical"
  exit 0
fi

# Search for the alias
canonical=$(jq -r --arg name "$model_name" '
  to_entries[]
  | select(.value.alias == $name)
  | .key
' "$json_file")

if [ -n "$canonical" ]; then
  echo "$canonical"
  exit 0
else
  echo "Canonical model for '$model_name' not found." >&2
  exit 1
fi
