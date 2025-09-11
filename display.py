#!/usr/bin/env python3
"""
Display functions for dejavu2-cli.

This module handles various display functions for showing information 
about the current status, models, templates, and other state.
"""
import click
from typing import Dict, Any, List

def display_status(
    kwargs: Dict[str, Any], 
    query_texts: List[str], 
    config: Dict[str, Any], 
    model_parameters: Dict[str, Any], 
    print_full_systemprompt: bool = False,
    conversation = None
) -> None:
    """
    Display comprehensive status information about the current configuration and settings.
    
    Args:
        kwargs: Command-line arguments dictionary
        query_texts: List of query texts
        config: Configuration dictionary
        model_parameters: Model parameters dictionary
        print_full_systemprompt: Whether to print the full system prompt regardless of length
    """
    kwargs['systemprompt'] = kwargs['systemprompt'].strip()
    
    # Section 1: Configuration
    click.echo("\n=== CONFIGURATION ===")
    if 'config_file' in config:
        click.echo(f"Config File: {config['config_file']}")
    click.echo(f"Template: {kwargs['template']}")
    
    # Section 2: Model Information
    click.echo("\n=== MODEL INFORMATION ===")
    click.echo(f"Selected Model/Alias: {kwargs['model']}")
    canonical_model = model_parameters.get('model', 'Unknown')
    click.echo(f"Canonical Model: {canonical_model}")
    click.echo(f"Provider: {model_parameters.get('parent', 'Unknown')}")
    click.echo(f"Family: {model_parameters.get('family', 'Unknown')}")
    click.echo(f"Context Window: {model_parameters.get('context_window', 'Unknown')}")
    click.echo(f"Max Output Tokens: {model_parameters.get('max_output_tokens', 'Unknown')}")
    
    # Section 3: API Status
    click.echo("\n=== API STATUS ===")
    api_key_type = model_parameters.get('apikey', 'Unknown')
    if api_key_type == 'OPENAI_API_KEY':
        api_status = "Present" if model_parameters.get('api_key_valid', False) else "Missing"
        click.echo(f"OpenAI API: Key {api_status}")
    elif api_key_type == 'ANTHROPIC_API_KEY':
        api_status = "Present" if model_parameters.get('api_key_valid', False) else "Missing"
        click.echo(f"Anthropic API: Key {api_status}")
    elif api_key_type == 'GOOGLE_API_KEY':
        api_status = "Present" if model_parameters.get('api_key_valid', False) else "Missing"
        click.echo(f"Google API: Key {api_status}")
    else:
        click.echo(f"API Type: {api_key_type}")
    
    # Section 4: Query Parameters
    click.echo("\n=== QUERY PARAMETERS ===")
    click.echo(f"Temperature: {kwargs['temperature']}")
    click.echo(f"Max Tokens: {kwargs['max_tokens']}")
    click.echo(f"Reference Files: {kwargs['reference'] if kwargs['reference'] else 'None'}")
    click.echo(f"Knowledgebase: {kwargs['knowledgebase'] if kwargs['knowledgebase'] else 'None'}")
    
    # Section 5: Query Content
    click.echo("\n=== QUERY CONTENT ===")
    
    # Handle system prompt length intelligently
    system_prompt = kwargs['systemprompt']
    prompt_lines = system_prompt.split('\n')
    prompt_length = len(prompt_lines)
    
    if print_full_systemprompt or prompt_length <= 10:
        # Show full prompt if requested or if it's short
        click.echo(f"System Prompt: '''\n{system_prompt}\n'''")
    else:
        # Show truncated version for long prompts
        preview_lines = prompt_lines[:3]
        preview_text = '\n'.join(preview_lines)
        chars_total = len(system_prompt)
        lines_hidden = prompt_length - 6  # We show 3 at start and 3 at end
        
        # Calculate size of hidden content
        if lines_hidden > 0:
            chars_hidden = len('\n'.join(prompt_lines[3:-3]))
            hidden_msg = f"[... {lines_hidden} lines ({chars_hidden} chars) hidden ...]"
            end_lines = '\n'.join(prompt_lines[-3:])
        else:
            hidden_msg = ""
            end_lines = ""
        
        click.echo(f"System Prompt: (long: {prompt_length} lines, {chars_total} chars) '''\n{preview_text}\n{hidden_msg}\n{end_lines}\n'''")
        click.echo(f"Use --print-systemprompt to see full system prompt")
    
    # Handle query display
    formatted_queries = [qt.strip() for qt in query_texts]
    if len(formatted_queries) == 1 and len(formatted_queries[0]) > 500:
        # Truncate very long queries
        query_preview = formatted_queries[0][:500]
        click.echo(f"Query: (truncated, {len(formatted_queries[0])} chars) '''\n{query_preview}...\n'''")
    else:
        click.echo(f"Query: '''\n{formatted_queries}\n'''")
    
    # Show other parameters
    other_params = []
    skip_keys = {'systemprompt', 'query_text', 'status', 'list_template', 'list_template_names', 
                'list_models', 'list_knowledge_bases', 'edit_defaults', 'edit_templates', 
                'edit_models', 'list_models_details', 'model', 'temperature', 'max_tokens', 
                'reference', 'knowledgebase', 'template', 'completions', 
                'continue_conv', 'conversation_id', 'list_conversations', 'delete_conversation',
                'new_conversation', 'title', 'export_conversation', 'export_path', 'stdout',
                'list_messages', 'remove_message', 'remove_pair',
                'verbose', 'log_file', 'quiet',
                'logging'}
    
    for key, value in kwargs.items():
        if key not in skip_keys:
            other_params.append((key, value))
    
    if other_params:
        click.echo("\n=== OTHER PARAMETERS ===")
        for key, value in other_params:
            click.echo(f"{key}: {value if value else 'None'}")
            
    # Display conversation information if available
    if conversation:
        click.echo("\n=== CONVERSATION ===")
        click.echo(f"ID: {conversation.id}")
        click.echo(f"Title: {conversation.title or 'Untitled'}")
        click.echo(f"Messages: {len(conversation.messages)}")
        click.echo(f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}")
        click.echo(f"Last Updated: {conversation.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Display metadata if available
        if conversation.metadata:
          click.echo("\nMetadata:")
          for key, value in conversation.metadata.items():
            click.echo(f"  {key}: {value}")
        
        # Show a preview of the conversation
        if len(conversation.messages) > 0:
          click.echo("\nPreview of last exchanges:")
          # Skip system messages in preview
          preview_msgs = [m for m in conversation.messages if m.role != "system"]
          # Show the last 3 messages (or all if fewer than 3)
          for msg in preview_msgs[-3:]:
            content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            click.echo(f"  {msg.role.capitalize()}: {content_preview}")