#!/usr/bin/env python3
"""
Context handling for dejavu2-cli.

This module handles retrieving and formatting additional context from reference files 
and knowledge bases for LLM queries.
"""
import os
import sys
import click
import subprocess
import logging
import xml.sax.saxutils
from glob import glob
from typing import Optional

logger = logging.getLogger(__name__)

def get_reference_string(reference: str) -> str:
    """
    Process reference files and return their contents as an XML-formatted string.
    
    Takes a comma-separated list of file paths, reads each file,
    and formats the contents as XML reference elements.
    
    Args:
        reference: A comma-separated list of file paths to include as references
        
    Returns:
        String containing the formatted reference content, or empty string if no reference
        
    Raises:
        FileNotFoundError: If any of the reference files cannot be found
        IOError: If there's an error reading any of the files
    """
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
            click.echo(f"File not found: '{file_name}'", err=True)
            raise
        except IOError as e:
            click.echo(f"Cannot read '{file_name}': {e}", err=True)
            raise
    return reference_string


def get_knowledgebase_string(
    knowledgebase: str, 
    knowledgebase_query: str,
    customkb_executable: str,
    vectordbs_path: str,
    api_keys: dict
) -> str:
    """
    Retrieve and return context from the specified knowledge base as an XML-formatted string.
    
    Uses the customKB executable to query the knowledge base and format the results.
    
    Args:
        knowledgebase: Name or path of the knowledge base (.cfg file)
        knowledgebase_query: Query to send to the knowledge base
        customkb_executable: Path to the customKB executable
        vectordbs_path: Path to look for knowledge base files
        api_keys: Dictionary of API keys to pass to the subprocess environment
        
    Returns:
        String containing the formatted knowledge base results, or empty string if no knowledge base
        
    Raises:
        FileNotFoundError: If the knowledge base cannot be found
        subprocess.CalledProcessError: If the customKB query fails
        Exception: For other unexpected errors
    """
    if not knowledgebase:
        return ''
        
    # Handle various knowledgebase path formats
    if not knowledgebase.endswith('.cfg'):
        # Could be a simple name, a relative path or a structured path
        if '/' in knowledgebase:
            # Path-like format (e.g., "okusi/okusiassociates")
            # This is already handled in the calling code to create full path
            pass
        else:
            # Simple name without path, append .cfg
            knowledgebase = f"{knowledgebase}.cfg"
            
    # Search for the knowledgebase file if it doesn't exist directly
    if not os.path.exists(knowledgebase):
        # Try with VECTORDBS_PATH environment variable if set
        vectordbs_env = os.environ.get('VECTORDBS', vectordbs_path)
        search_pattern = os.path.join(vectordbs_env, '**', os.path.basename(knowledgebase))
        matches = glob(search_pattern, recursive=True)
        if matches:
            knowledgebase = matches[0]
        else:
            # Fallback to default path
            search_pattern = os.path.join(vectordbs_path, '**', os.path.basename(knowledgebase))
            matches = glob(search_pattern, recursive=True)
            if matches:
                knowledgebase = matches[0]
            else:
                logger.error(f"Knowledgebase file '{knowledgebase}' not found in {vectordbs_path}")
                raise FileNotFoundError(f"Knowledgebase file '{knowledgebase}' not found")

    try:
        # Set environment variables for the subprocess
        env = os.environ.copy()
        
        # Make sure we pass the API keys to the subprocess
        for key, value in api_keys.items():
            if value:
                env[key] = value
        
        logger.info(f"Running customkb query with: {customkb_executable} query {knowledgebase} {knowledgebase_query} --context")
        
        result = subprocess.run(
            [customkb_executable, 'query', knowledgebase, knowledgebase_query, '--context'],
            capture_output=True, text=True, check=True, env=env
        )
        return f'<knowledgebase>\n{result.stdout.strip()}\n</knowledgebase>\n\n'
    except subprocess.CalledProcessError as e:
        logger.error(f"Error querying knowledgebase: {e.stderr.strip()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying knowledgebase: {e}")
        raise


def list_knowledge_bases(vectordbs_path: str) -> list:
    """
    List all available knowledge bases in the specified directory.
    
    Recursively searches for .cfg files in the vectordbs_path directory and
    displays their names in alphabetical order.
    
    Args:
        vectordbs_path: Path to the directory containing knowledge base files
        
    Returns:
        List of canonical paths to knowledge base files
        
    Raises:
        ValueError: If the vectordbs_path is not a valid directory
    """
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
        click.echo("Available Knowledge Bases:")
        for kb in sorted_kb_names:
            click.echo(f"  {kb}")
    else:
        click.echo("No knowledgebases found.")

    return list(knowledge_bases)