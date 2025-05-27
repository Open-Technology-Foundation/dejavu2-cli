#!/usr/bin/env python3
"""
Template handling for dejavu2-cli.

This module handles loading, displaying and applying templates from Agents.json.
Templates define reusable configurations for LLM queries.
"""
import os
import sys
import json
import click
import logging
from typing import Dict, Any, Optional, Tuple, List

from errors import ConfigurationError, TemplateError

# Configure module logger
logger = logging.getLogger(__name__)

def normalize_key(key: str) -> str:
    """
    Normalize a template key for case-insensitive, fuzzy matching.
    
    Transforms the key by:
    1. Taking only the part before any '-' character
    2. Converting to lowercase
    3. Removing spaces and underscores
    
    Args:
        key: The original template key/name
        
    Returns:
        Normalized version of the key for comparison
    """
    key = key.split('-')[0].strip()
    return key.lower().replace(' ', '').replace('_', '')

def load_template_data(template_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load and return data from the templates file (Agents.json).
    
    Reads the templates file and parses it as JSON.
    
    Args:
        template_path: Path to the templates file
        
    Returns:
        Dictionary containing template definitions, with template names as keys
        
    Raises:
        ConfigurationError: If the templates file cannot be found or accessed
        TemplateError: If the file contains invalid JSON or format
    """
    if not os.path.exists(template_path):
        error_msg = f"Template file not found: {template_path}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
        
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            templates = json.load(file)
    except (OSError, IOError) as e:
        error_msg = f"Error reading template file {template_path}: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in template file {template_path}: {str(e)}"
        logger.error(error_msg)
        raise TemplateError(error_msg)
    
    if not isinstance(templates, dict):
        error_msg = f"Invalid template format in {template_path}. Expected JSON object, got {type(templates).__name__}"
        logger.error(error_msg)
        raise TemplateError(error_msg)
        
    return templates

def get_template(template_key: str, template_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Retrieve a template by its key, using fuzzy matching for the lookup.
    
    Attempts to find a template that matches the specified key, using
    normalization for comparison with options in the template file.
    
    Args:
        template_key: Key/name of the template to retrieve
        template_path: Path to the templates file
        
    Returns:
        Tuple of (original_key, template_data) if found
        
    Raises:
        ConfigurationError: If the templates file cannot be found or accessed
        TemplateError: If the template key is invalid or template not found
    """
    if not template_key or not template_key.strip():
        error_msg = "Template key cannot be empty or whitespace"
        logger.error(error_msg)
        raise TemplateError(error_msg)
        
    templates = load_template_data(template_path)
    
    # Search in order of decreasing specificity:
    
    # 1. Exact match
    if template_key in templates:
        return template_key, templates[template_key]
    
    # 2. Match using normalized keys
    normalized_search = normalize_key(template_key)
    for key, value in templates.items():
        if normalize_key(key) == normalized_search:
            return key, value
    
    # 3. Substring match with normalized keys
    for key, value in templates.items():
        if normalized_search in normalize_key(key):
            return key, value
    
    # Template not found
    available_templates = list(templates.keys())
    error_msg = f"Template '{template_key}' not found. Available templates: {', '.join(available_templates)}"
    logger.error(error_msg)
    raise TemplateError(error_msg)

def print_template(name: str, data: Dict[str, Any]) -> None:
    """
    Print the specified template's name and its details in a readable format.
    
    Args:
        name: Name of the template
        data: Dictionary containing the template's properties
    """
    click.echo(f"Template: {name}")
    for key, value in data.items():
        if key == 'systemprompt':
            click.echo(f'  {key}: """\n{value}\n"""')
        elif key != 'monospace':
            click.echo(f"  {key}: {value}")
    click.echo()

def list_template_names(template_path: str) -> List[str]:
    """
    List the names and basic details of all templates in a columnar format.
    
    Displays a table with template names, models, temperature settings,
    token limits, and knowledge base settings.
    
    Args:
        template_path: Path to the templates file
        
    Returns:
        List of template names sorted alphabetically
        
    Raises:
        ConfigurationError: If the templates file cannot be found or accessed
        TemplateError: If the templates file contains invalid JSON or format
    """
    data = load_template_data(template_path)
        
    sorted_names = sorted(data.keys(), key=str.casefold)
    
    # Define table columns and their corresponding template keys
    columns = [
        ('Template Name', 'name'),
        ('Model', 'model'),
        ('Temp', 'temperature'),
        ('Tokens', 'max_tokens'),
        ('Knowledge Base', 'knowledgebase')
    ]
    
    # Calculate the maximum width needed for each column
    max_lengths = {col_name: len(col_name) for col_name, _ in columns}
    for template_name in sorted_names:
        template_data = data[template_name]
        for col_name, key in columns:
            value = template_name if key == 'name' else template_data.get(key, 'N/A')
            max_lengths[col_name] = max(max_lengths[col_name], len(str(value)))

    # Print header
    header = '  '.join(f"{col_name:<{max_lengths[col_name]}}" for col_name, _ in columns)
    click.echo(header)
    click.echo('-' * len(header))

    # Print each template row
    for template_name in sorted_names:
        template_data = data[template_name]
        row = []
        for col_name, key in columns:
            value = template_name if key == 'name' else template_data.get(key, 'N/A')
            row.append(f"{value:<{max_lengths[col_name]}}")
        click.echo('  '.join(row))
    
    return sorted_names

def list_templates(template_path: str, template: Optional[str] = None, names_only: bool = False) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    List all templates or details of a specific template.
    
    Args:
        template_path: Path to the templates file
        template: If provided, displays details for just this template.
                  If 'all' or None, displays all templates.
        names_only: If True, uses the more concise list_template_names format
                  
    Returns:
        Dictionary of templates organized by category
        
    Raises:
        ConfigurationError: If the templates file cannot be found or accessed
        TemplateError: If the templates file contains invalid JSON or format
    """
    data = load_template_data(template_path)

    # If only names requested, use the list_template_names function
    if names_only:
        list_template_names(template_path)
        return {}

    # If a specific template is requested
    if template and template != 'all':
        template_found = False
        normalized_template = normalize_key(template)
        
        # First try exact match
        if template in data:
            print_template(template, data[template])
            template_found = True
        else:
            # Try normalized matching
            for key, value in data.items():
                if normalize_key(key) == normalized_template:
                    print_template(key, value)
                    template_found = True
                    break
        
        if not template_found:
            available_templates = list(data.keys())
            error_msg = f"Template '{template}' not found. Available templates: {', '.join(available_templates)}"
            logger.error(error_msg)
            raise TemplateError(error_msg)
        
        return {}
    
    # Organize templates by category for return value
    templates_by_category = {}
    
    # Display all templates sorted by name
    for template_name, template_data in sorted(data.items(), key=lambda x: str.casefold(x[0])):
        print_template(template_name, template_data)
        
        # Add to category dictionary for return value
        category = template_data.get('category', 'Uncategorized')
        if category not in templates_by_category:
            templates_by_category[category] = {}
        templates_by_category[category][template_name] = template_data
    
    return templates_by_category