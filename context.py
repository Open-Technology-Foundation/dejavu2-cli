#!/usr/bin/env python3
"""
Context handling for dejavu2-cli.

This module handles retrieving and formatting additional context from reference files
and knowledgebases for LLM queries.
"""

import logging
import os
import subprocess
import xml.sax.saxutils
from glob import glob
from pathlib import Path

import click

from errors import KnowledgeBaseError, ReferenceError

# Import security functions
from security import SecurityError, ValidationError, get_knowledgebase_subprocess, validate_file_path, validate_knowledgebase_query

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
      ReferenceError: If any of the reference files cannot be found, read, or contain invalid paths
  """
  if not reference:
    return ""

  reference_string = ""
  reference_files = [file_name.strip() for file_name in reference.split(",")]

  for file_name in reference_files:
    try:
      # Validate file path for security
      safe_file_path = validate_file_path(file_name, must_exist=True)

      base_name = Path(safe_file_path).stem
      # Escape the base name for XML safety
      safe_base_name = xml.sax.saxutils.escape(base_name)

      with open(safe_file_path, encoding="utf-8") as f:
        reference_content = f.read().strip()
        # Escape content for XML safety
        reference_content = xml.sax.saxutils.escape(reference_content)

      reference_string += f'<reference name="{safe_base_name}">\n{reference_content}\n</reference>\n\n'

    except ValidationError as e:
      error_msg = f"Invalid reference file path '{file_name}': {e}"
      logger.error(error_msg)
      raise ReferenceError(error_msg) from e
    except FileNotFoundError as e:
      error_msg = f"Reference file not found: '{file_name}'"
      logger.error(error_msg)
      raise ReferenceError(error_msg) from e
    except OSError as e:
      error_msg = f"Cannot read reference file '{file_name}': {e}"
      logger.error(error_msg)
      raise ReferenceError(error_msg) from e
    except UnicodeDecodeError as e:
      error_msg = f"Cannot decode reference file '{file_name}': {e}"
      logger.error(error_msg)
      raise ReferenceError(error_msg) from e

  return reference_string


def get_knowledgebase_string(knowledgebase: str, knowledgebase_query: str, customkb_executable: str, vectordbs_path: str, api_keys: dict) -> str:
  """
  Retrieve and return context from the specified knowledgebase as an XML-formatted string.

  Uses the customKB executable to query the knowledgebase and format the results.

  Args:
      knowledgebase: Name or path of the knowledgebase (.cfg file)
      knowledgebase_query: Query to send to the knowledgebase
      customkb_executable: Path to the customKB executable
      vectordbs_path: Path to look for knowledgebase files
      api_keys: Dictionary of API keys to pass to the subprocess environment

  Returns:
      String containing the formatted knowledgebase results, or empty string if no knowledgebase

  Raises:
      KnowledgeBaseError: If the knowledgebase cannot be found, executed, or contains invalid paths/queries
  """
  if not knowledgebase:
    return ""

  try:
    # Validate and sanitize the query input
    safe_query = validate_knowledgebase_query(knowledgebase_query)

    # Validate the customkb executable path
    safe_executable = validate_file_path(customkb_executable, must_exist=True)

    # Handle various knowledgebase path formats
    if not knowledgebase.endswith(".cfg"):
      # Could be a simple name, a relative path or a structured path
      if "/" in knowledgebase:
        # Path-like format (e.g., "okusi/okusiassociates")
        # This is already handled in the calling code to create full path
        pass
      else:
        # Simple name without path, append .cfg
        knowledgebase = f"{knowledgebase}.cfg"

    # Validate the knowledgebase path
    safe_knowledgebase = validate_file_path(knowledgebase)

    # Search for the knowledgebase file if it doesn't exist directly
    if not Path(safe_knowledgebase).exists():
      # Try with VECTORDBS_PATH environment variable if set
      vectordbs_env = os.environ.get("VECTORDBS", vectordbs_path)
      search_pattern = str(Path(vectordbs_env) / "**" / Path(safe_knowledgebase).name)
      matches = glob(search_pattern, recursive=True)
      if matches:
        safe_knowledgebase = validate_file_path(matches[0], must_exist=True)
      else:
        # Fallback to default path
        search_pattern = str(Path(vectordbs_path) / "**" / Path(safe_knowledgebase).name)
        matches = glob(search_pattern, recursive=True)
        if matches:
          safe_knowledgebase = validate_file_path(matches[0], must_exist=True)
        else:
          error_msg = f"Knowledgebase file '{knowledgebase}' not found in {vectordbs_path}"
          logger.error(error_msg)
          raise KnowledgeBaseError(error_msg)

    # Get secure subprocess for knowledgebase operations
    secure_subprocess = get_knowledgebase_subprocess()

    # Update environment whitelist to include the API keys that are actually set
    if secure_subprocess.config.environment_whitelist:
      env_vars = []
      for key in secure_subprocess.config.environment_whitelist:
        if key in api_keys and api_keys[key]:
          env_vars.append(key)
      secure_subprocess.config.environment_whitelist = env_vars

    logger.info(f"Running secure customkb query: {Path(safe_executable).name} query [knowledgebase] [query] --context")

    # Execute with security validation
    result = secure_subprocess.run([safe_executable, "query", safe_knowledgebase, safe_query, "--context", "--quiet"])

    # Escape the output for XML safety
    safe_output = xml.sax.saxutils.escape(result.stdout.strip())
    return f"<knowledgebase>\n{safe_output}\n</knowledgebase>\n\n"

  except ValidationError as e:
    error_msg = f"Invalid knowledgebase query: {e}"
    logger.error(error_msg)
    raise KnowledgeBaseError(error_msg) from e
  except SecurityError as e:
    error_msg = f"Security error in knowledgebase query: {e}"
    logger.error(error_msg)
    raise KnowledgeBaseError(error_msg) from e
  except subprocess.CalledProcessError as e:
    error_msg = f"Knowledgebase executable failed: {e}"
    logger.error(error_msg)
    raise KnowledgeBaseError(error_msg) from e
  except OSError as e:
    error_msg = f"Error executing knowledgebase query: {e}"
    logger.error(error_msg)
    raise KnowledgeBaseError(error_msg) from e
  except Exception as e:
    error_msg = f"Unexpected error querying knowledgebase: {e}"
    logger.error(error_msg)
    raise KnowledgeBaseError(error_msg) from e


def list_knowledge_bases(vectordbs_path: str) -> list:
  """
  List all available knowledgebases in the specified directory.

  Recursively searches for .cfg files in the vectordbs_path directory and
  displays their names in alphabetical order.

  Args:
      vectordbs_path: Path to the directory containing knowledgebase files

  Returns:
      List of canonical paths to knowledgebase files

  Raises:
      KnowledgeBaseError: If the vectordbs_path is not a valid directory
  """
  if not Path(vectordbs_path).is_dir():
    error_msg = f"Knowledgebase directory '{vectordbs_path}' is not a valid directory"
    logger.error(error_msg)
    raise KnowledgeBaseError(error_msg)

  knowledge_bases = set()  # Using set to automatically handle duplicates
  search_path = str(Path(vectordbs_path) / "**" / "*.cfg")

  # Get all .cfg files and resolve to canonical paths
  for cfg_file in glob(search_path, recursive=True):
    canonical_path = str(Path(cfg_file).resolve())  # Resolves symlinks to real path
    knowledge_bases.add(canonical_path)

  # Convert set back to sorted list
  knowledge_bases = sorted(knowledge_bases)

  if knowledge_bases:
    sorted_kb_names = sorted([Path(kb).stem for kb in knowledge_bases])
    click.echo("Available Knowledgebases:")
    for kb in sorted_kb_names:
      click.echo(f"  {kb}")
  else:
    click.echo("No knowledgebases found.")

  return list(knowledge_bases)
