#!/usr/bin/env python3
"""
Configuration handling for dejavu2-cli.

This module handles loading and managing configuration from:
- Default config file (defaults.yaml)
- User config file (~/.config/dejavu2-cli/config.yaml)
- Command-line options
"""

import json
import logging
import os
import shutil
import tempfile

import click
import yaml

# Import security functions
from security import SecurityError, ValidationError, get_editor_subprocess, validate_editor_path

# Configure module logger
logger = logging.getLogger(__name__)


def load_config(default_config_path, user_config_path=None):
  """
  Load and return configuration from default and user YAML files.

  Args:
      default_config_path: Path to the default config file
      user_config_path: Path to the user config file (optional)

  Returns:
      Dict containing merged configuration

  Raises:
      FileNotFoundError: If required config files are missing
      yaml.YAMLError: If config files contain invalid YAML
  """
  config = {}

  # Load default configuration (required)
  logger.debug(f"Loading default config from: {default_config_path}")
  if not os.path.exists(default_config_path):
    error_msg = f"Default config not found: {default_config_path}"
    logger.error(error_msg)
    click.echo(f"Error: {error_msg}", err=True)
    raise FileNotFoundError(f"Default config file not found: {default_config_path}")

  try:
    with open(default_config_path, encoding="utf-8") as f:
      config = yaml.safe_load(f) or {}
      config["config_file"] = default_config_path
      logger.debug(f"Loaded default config with {len(config)} keys")
  except yaml.YAMLError as e:
    error_msg = f"Invalid default config: {e}"
    logger.error(error_msg)
    click.echo(f"Error: {error_msg}", err=True)
    raise
  except PermissionError as e:
    error_msg = f"Permission denied reading default config: {e}"
    logger.error(error_msg)
    click.echo(f"Error: {error_msg}", err=True)
    raise
  except (IOError, OSError) as e:
    error_msg = f"I/O error loading default config: {e}"
    logger.error(error_msg)
    click.echo(f"Error: {error_msg}", err=True)
    raise
  except UnicodeDecodeError as e:
    error_msg = f"Encoding error in default config: {e}"
    logger.error(error_msg)
    click.echo(f"Error: {error_msg}", err=True)
    raise

  # Update with user configuration if it exists
  if user_config_path and os.path.exists(user_config_path):
    logger.debug(f"Loading user config from: {user_config_path}")
    try:
      with open(user_config_path, encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

        # Recursively merge nested dictionaries
        for key, value in user_config.items():
          if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            config[key].update(value)
            logger.debug(f"Merged nested dict for key: {key}")
          else:
            config[key] = value
            logger.debug(f"Set/overrode key: {key}")

        config["config_file"] = user_config_path
        logger.debug(f"Updated config with user settings from {user_config_path}")
    except yaml.YAMLError as e:
      error_msg = f"Invalid user config: {e}"
      logger.error(error_msg)
      click.echo(f"Error: {error_msg}", err=True)
      raise
    except PermissionError as e:
      error_msg = f"Permission denied reading user config: {e}"
      logger.error(error_msg)
      click.echo(f"Error: {error_msg}", err=True)
      raise
    except (IOError, OSError) as e:
      error_msg = f"I/O error loading user config: {e}"
      logger.error(error_msg)
      click.echo(f"Error: {error_msg}", err=True)
      raise
    except UnicodeDecodeError as e:
      error_msg = f"Encoding error in user config: {e}"
      logger.error(error_msg)
      click.echo(f"Error: {error_msg}", err=True)
      raise

  # Validate required keys
  required_keys = ["paths", "defaults"]
  missing_keys = [key for key in required_keys if key not in config]
  if missing_keys:
    error_msg = f"Required configuration keys missing: {', '.join(missing_keys)}"
    logger.error(error_msg)
    click.echo(f"Error: {error_msg}", err=True)
    raise KeyError(error_msg)

  # Ensure API keys section exists even if not in config
  if "api_keys" not in config:
    config["api_keys"] = {}

  return config


def edit_yaml_file(filename: str):
  """
  Edit the specified YAML file using the system's default editor or 'nano'.

  Creates a temporary copy of the file, opens it in the editor, validates
  the YAML syntax, and replaces the original file if valid.

  Args:
      filename: Path to the YAML file to edit

  Raises:
      ValidationError: If the editor path or file path is invalid
      SecurityError: If the subprocess execution fails
      yaml.YAMLError: If the edited file contains invalid YAML
  """
  try:
    # Get and validate editor
    editor = os.environ.get("EDITOR", "nano").strip()
    safe_editor = validate_editor_path(editor)

    # Get secure subprocess for editor operations
    secure_subprocess = get_editor_subprocess()

    # Create a temporary copy of the file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp_file:
      temp_path = temp_file.name
      shutil.copy2(filename, temp_path)

    try:
      while True:
        try:
          # Open the temporary file in the editor with security validation
          secure_subprocess.run([safe_editor, temp_path])

          # Validate the YAML syntax
          with open(temp_path, encoding="utf-8") as f:
            yaml.safe_load(f)

          # If valid, replace the original file
          shutil.move(temp_path, filename)
          click.echo(f"{filename} edited and updated successfully.")
          break

        except SecurityError as e:
          click.echo(f"Error: Security issue with editor execution: {e}", err=True)
          break
        except yaml.YAMLError as e:
          click.echo(f"Error: Invalid YAML in edited file.\nDetails: {e}", err=True)
          if not click.confirm("Do you want to re-edit the file?"):
            click.echo("Changes discarded.")
            break
    finally:
      # Clean up temporary file
      if os.path.exists(temp_path):
        os.unlink(temp_path)

  except ValidationError as e:
    click.echo(f"Error: Invalid editor configuration: {e}", err=True)
    raise
  except PermissionError as e:
    click.echo(f"Error: Permission denied during file editing: {e}", err=True)
    raise
  except OSError as e:
    click.echo(f"Error: I/O error during file editing: {e}", err=True)
    raise
  except shutil.Error as e:
    click.echo(f"Error: File operation error during editing: {e}", err=True)
    raise


def edit_json_file(filename: str):
  """
  Edit the specified JSON file using the system's default editor or 'nano'.

  Creates a temporary copy of the file, opens it in the editor, validates
  the JSON syntax, and replaces the original file if valid.

  Args:
      filename: Path to the JSON file to edit

  Raises:
      ValidationError: If the editor path or file path is invalid
      SecurityError: If the subprocess execution fails
      json.JSONDecodeError: If the edited file contains invalid JSON
  """
  try:
    # Get and validate editor
    editor = os.environ.get("EDITOR", "nano").strip()
    safe_editor = validate_editor_path(editor)

    # Get secure subprocess for editor operations
    secure_subprocess = get_editor_subprocess()

    # Create a temporary copy of the file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
      temp_path = temp_file.name
      shutil.copy2(filename, temp_path)

    try:
      while True:
        try:
          # Open the temporary file in the editor with security validation
          secure_subprocess.run([safe_editor, temp_path])

          # Validate the JSON syntax
          with open(temp_path, encoding="utf-8") as f:
            json.load(f)

          # If valid, replace the original file
          shutil.move(temp_path, filename)
          click.echo(f"{filename} edited and updated successfully.")
          break

        except SecurityError as e:
          click.echo(f"Error: Security issue with editor execution: {e}", err=True)
          break
        except json.JSONDecodeError as e:
          click.echo(f"Error: Invalid JSON in edited file.\nDetails: {e}", err=True)
          if not click.confirm("Do you want to re-edit the file?"):
            click.echo("Changes discarded.")
            break
    finally:
      # Clean up temporary file
      if os.path.exists(temp_path):
        os.unlink(temp_path)

  except ValidationError as e:
    click.echo(f"Error: Invalid editor configuration: {e}", err=True)
    raise
  except PermissionError as e:
    click.echo(f"Error: Permission denied during file editing: {e}", err=True)
    raise
  except OSError as e:
    click.echo(f"Error: I/O error during file editing: {e}", err=True)
    raise
  except shutil.Error as e:
    click.echo(f"Error: File operation error during editing: {e}", err=True)
    raise
