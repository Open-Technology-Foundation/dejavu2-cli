#!/usr/bin/env python3
"""
Check Models.json for errors and duplications
"""

import json
import sys
from collections import Counter

MODELS_PATH = "Models.json"

def check_models_json():
    """Check Models.json for errors and duplications"""
    
    # Load the models data
    try:
        with open(MODELS_PATH, 'r') as f:
            models = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Models.json is not valid JSON: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to read Models.json: {e}")
        return 1
    
    print(f"Loaded {len(models)} models from Models.json")
    
    # Check for model ID duplication
    model_ids = list(models.keys())
    if len(model_ids) != len(set(model_ids)):
        print("ERROR: Duplicate model IDs found:")
        duplicates = [item for item, count in Counter(model_ids).items() if count > 1]
        for dup in duplicates:
            print(f"  - {dup}")
    
    # Check for alias duplication
    aliases = []
    for model_id, model_data in models.items():
        alias = model_data.get("alias")
        if alias:
            aliases.append((alias, model_id))
    
    alias_names = [a[0] for a in aliases]
    dup_aliases = [item for item, count in Counter(alias_names).items() if count > 1]
    
    if dup_aliases:
        print("\nWARNING: Duplicate aliases found:")
        for dup in dup_aliases:
            models_with_alias = [model_id for alias, model_id in aliases if alias == dup]
            print(f"  - '{dup}' is used by {len(models_with_alias)} models:")
            for model_id in models_with_alias:
                parent = models[model_id].get("parent", "Unknown")
                print(f"    - {model_id} (parent: {parent})")
    
    # Check for missing required fields
    required_fields = ["model", "alias", "parent", "model_category", "family", "series", 
                      "url", "apikey", "available", "enabled"]
    
    models_with_missing_fields = []
    for model_id, model_data in models.items():
        missing = [field for field in required_fields if field not in model_data]
        if missing:
            models_with_missing_fields.append((model_id, missing))
    
    if models_with_missing_fields:
        print("\nWARNING: Models with missing required fields:")
        for model_id, missing in models_with_missing_fields:
            print(f"  - {model_id}: missing {', '.join(missing)}")
    
    # Check for wrong field types
    type_issues = []
    for model_id, model_data in models.items():
        if "context_window" in model_data and not isinstance(model_data["context_window"], (int, type(None))):
            type_issues.append(f"{model_id}: context_window should be integer, got {type(model_data['context_window'])}")
        
        if "max_output_tokens" in model_data and not isinstance(model_data["max_output_tokens"], (int, type(None))):
            type_issues.append(f"{model_id}: max_output_tokens should be integer, got {type(model_data['max_output_tokens'])}")
        
        if "vision" in model_data and not isinstance(model_data["vision"], int):
            type_issues.append(f"{model_id}: vision should be integer, got {type(model_data['vision'])}")
        
        if "available" in model_data and not isinstance(model_data["available"], int):
            type_issues.append(f"{model_id}: available should be integer, got {type(model_data['available'])}")
        
        if "enabled" in model_data and not isinstance(model_data["enabled"], int):
            type_issues.append(f"{model_id}: enabled should be integer, got {type(model_data['enabled'])}")
    
    if type_issues:
        print("\nWARNING: Type issues detected:")
        for issue in type_issues:
            print(f"  - {issue}")
    
    # Check providers
    providers = Counter([model.get("parent") for model in models.values()])
    print("\nProvider breakdown:")
    for provider, count in providers.items():
        print(f"  - {provider}: {count} models")
    
    # Summary
    if not (dup_aliases or models_with_missing_fields or type_issues):
        print("\nNo issues found! Models.json looks good.")
    else:
        print("\nIssues found in Models.json. Please correct them.")
    
    return 0

if __name__ == "__main__":
    sys.exit(check_models_json())