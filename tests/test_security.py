#!/usr/bin/env python3
"""
Security tests for dejavu2-cli.

This module tests the security validation functions and secure subprocess wrapper
to ensure protection against command injection and other security vulnerabilities.
"""
import pytest
import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from security import (
    validate_knowledgebase_query, 
    validate_editor_path,
    validate_file_path,
    SecureSubprocess,
    SubprocessConfig,
    ValidationError,
    SecurityError,
    get_knowledgebase_subprocess,
    get_editor_subprocess,
    escape_for_shell
)

class TestKnowledgeBaseValidation:
  """Test knowledgebase query validation."""
  
  def test_valid_queries_pass(self):
    """Test that valid queries pass validation."""
    valid_queries = [
      "simple query",
      "query with numbers 123",
      "query-with-dashes_and_underscores",
      "query with punctuation: .?!",
      "Query with (parentheses) and [brackets]",
      "Query with quotes 'single' and \"double\"",
      "Query with symbols @#%^&*+=~",
      "Multi-word query about Python programming",
    ]
    for query in valid_queries:
      result = validate_knowledgebase_query(query)
      assert result == query.strip()
  
  def test_dangerous_queries_rejected(self):
    """Test that dangerous queries are rejected."""
    dangerous_queries = [
      "query; rm -rf /",
      "query && malicious_command",
      "query | cat /etc/passwd",
      "query `whoami`",
      "query $(rm -rf /)",
      "query ${HOME}/.ssh/id_rsa",
      "query > /etc/passwd",
      "query < /dev/random",
      "query || echo 'hacked'",
      "query \\x41\\x42",  # Hex escape
      "query \\101\\102",  # Octal escape
    ]
    for query in dangerous_queries:
      with pytest.raises(ValidationError, match="dangerous pattern"):
        validate_knowledgebase_query(query)
  
  def test_empty_query_rejected(self):
    """Test that empty queries are rejected."""
    with pytest.raises(ValidationError, match="cannot be empty"):
      validate_knowledgebase_query("")
    with pytest.raises(ValidationError, match="cannot be empty"):
      validate_knowledgebase_query("   ")
    with pytest.raises(ValidationError, match="cannot be empty"):
      validate_knowledgebase_query("\t\n")
  
  def test_oversized_query_rejected(self):
    """Test that oversized queries are rejected."""
    large_query = "a" * 1001
    with pytest.raises(ValidationError, match="too long"):
      validate_knowledgebase_query(large_query)
  
  def test_invalid_characters_rejected(self):
    """Test that queries with invalid characters are rejected."""
    invalid_queries = [
      "query\x00null",  # Null character
      "query\x01control",  # Control character
      "query\u202e",  # Unicode override character
    ]
    for query in invalid_queries:
      with pytest.raises(ValidationError, match="invalid characters"):
        validate_knowledgebase_query(query)
  
  def test_whitespace_normalization(self):
    """Test that leading/trailing whitespace is stripped."""
    query = "  test query  "
    result = validate_knowledgebase_query(query)
    assert result == "test query"

class TestEditorValidation:
  """Test editor path validation."""
  
  def test_valid_editor_names(self):
    """Test validation of common editor names."""
    with patch('security.shutil.which') as mock_which:
      mock_which.return_value = '/usr/bin/nano'
      
      with patch('os.path.exists', return_value=True), \
           patch('os.path.isfile', return_value=True), \
           patch('os.access', return_value=True):
        
        result = validate_editor_path('nano')
        assert result == '/usr/bin/nano'
        mock_which.assert_called_once_with('nano')
  
  def test_valid_editor_paths(self, tmp_path):
    """Test validation of valid editor paths."""
    # Create a mock executable
    editor_path = tmp_path / "test_editor"
    editor_path.write_text("#!/bin/bash\necho 'editor'")
    editor_path.chmod(0o755)
    
    result = validate_editor_path(str(editor_path))
    assert result == str(editor_path.resolve())
  
  def test_dangerous_editor_paths_rejected(self):
    """Test that dangerous editor paths are rejected."""
    dangerous_paths = [
      "/bin/sh; rm -rf /",
      "/usr/bin/vim && malicious",
      "/usr/bin/nano | cat /etc/passwd",
      "/usr/bin/emacs `whoami`",
      "/usr/bin/vi $(whoami)",
      "/usr/bin/joe > /etc/passwd",
    ]
    for path in dangerous_paths:
      with pytest.raises(ValidationError, match="dangerous characters"):
        validate_editor_path(path)
  
  def test_empty_editor_path_rejected(self):
    """Test that empty editor paths are rejected."""
    with pytest.raises(ValidationError, match="cannot be empty"):
      validate_editor_path("")
    with pytest.raises(ValidationError, match="cannot be empty"):
      validate_editor_path("   ")
  
  def test_nonexistent_editor_rejected(self):
    """Test that non-existent editors are rejected."""
    with pytest.raises(ValidationError, match="not found"):
      validate_editor_path("/nonexistent/editor")
  
  def test_non_executable_editor_rejected(self, tmp_path):
    """Test that non-executable files are rejected."""
    # Create a non-executable file
    editor_path = tmp_path / "non_executable"
    editor_path.write_text("not executable")
    editor_path.chmod(0o644)  # Not executable
    
    with pytest.raises(ValidationError, match="not executable"):
      validate_editor_path(str(editor_path))

class TestFilePathValidation:
  """Test file path validation."""
  
  def test_valid_file_paths(self, tmp_path):
    """Test validation of valid file paths."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    result = validate_file_path(str(test_file), must_exist=True)
    assert result == str(test_file.resolve())
  
  def test_dangerous_file_paths_rejected(self):
    """Test that dangerous file paths are rejected."""
    dangerous_paths = [
      "/path; rm -rf /",
      "/path && malicious",
      "/path | cat /etc/passwd",
      "/path `whoami`",
      "/path $(rm -rf /)",
      "/path ${HOME}/.ssh/id_rsa",
    ]
    for path in dangerous_paths:
      with pytest.raises(ValidationError, match="dangerous pattern"):
        validate_file_path(path)
  
  def test_nonexistent_file_with_must_exist(self):
    """Test that non-existent files are rejected when must_exist=True."""
    with pytest.raises(ValidationError, match="does not exist"):
      validate_file_path("/nonexistent/file.txt", must_exist=True)
  
  def test_nonexistent_file_without_must_exist(self):
    """Test that non-existent files are allowed when must_exist=False."""
    result = validate_file_path("/nonexistent/file.txt", must_exist=False)
    assert result.endswith("file.txt")

class TestSecureSubprocess:
  """Test secure subprocess wrapper."""
  
  def test_command_whitelist_enforcement(self):
    """Test that only whitelisted commands are allowed."""
    config = SubprocessConfig(allowed_commands=['echo'])
    secure_subprocess = SecureSubprocess(config)
    
    # Should work for allowed commands
    with patch('subprocess.run') as mock_run:
      mock_run.return_value = MagicMock(stdout='hello', stderr='')
      secure_subprocess.run(['echo', 'hello'])
      mock_run.assert_called_once()
    
    # Should fail for disallowed commands
    with pytest.raises(ValidationError, match="not allowed"):
      secure_subprocess.run(['rm', '-rf', '/'])
  
  def test_argument_validation(self):
    """Test that dangerous arguments are rejected."""
    config = SubprocessConfig(allowed_commands=['echo'])
    secure_subprocess = SecureSubprocess(config)
    
    dangerous_args = [
      '; rm -rf /',
      '&& malicious_command',
      '| cat /etc/passwd',
      '`whoami`',
      '$(rm -rf /)',
      '${HOME}/.ssh/id_rsa',
    ]
    
    for arg in dangerous_args:
      with pytest.raises(ValidationError, match="dangerous pattern"):
        secure_subprocess.run(['echo', arg])
  
  def test_shell_disabled(self):
    """Test that shell=True is never used."""
    config = SubprocessConfig(allowed_commands=['echo'])
    secure_subprocess = SecureSubprocess(config)
    
    with patch('subprocess.run') as mock_run:
      mock_run.return_value = MagicMock(stdout='test', stderr='')
      secure_subprocess.run(['echo', 'test'], shell=True)  # Should be ignored
      
      # Verify shell=False was enforced
      call_args = mock_run.call_args
      assert call_args[1]['shell'] is False
  
  def test_timeout_enforcement(self):
    """Test that timeout is enforced."""
    config = SubprocessConfig(allowed_commands=['sleep'], timeout=1.0)
    secure_subprocess = SecureSubprocess(config)
    
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('sleep', 1.0)):
      with pytest.raises(SecurityError, match="timed out"):
        secure_subprocess.run(['sleep', '10'])
  
  def test_max_args_enforcement(self):
    """Test that maximum arguments limit is enforced."""
    config = SubprocessConfig(allowed_commands=['echo'], max_args=3)
    secure_subprocess = SecureSubprocess(config)
    
    # Should work with few arguments
    with patch('subprocess.run') as mock_run:
      mock_run.return_value = MagicMock(stdout='test', stderr='')
      secure_subprocess.run(['echo', 'arg1'])
    
    # Should fail with too many arguments
    with pytest.raises(ValidationError, match="Too many arguments"):
      secure_subprocess.run(['echo', 'arg1', 'arg2', 'arg3', 'arg4'])
  
  def test_environment_whitelist(self):
    """Test that environment variable whitelist is enforced."""
    config = SubprocessConfig(
      allowed_commands=['env'],
      environment_whitelist=['SAFE_VAR']
    )
    secure_subprocess = SecureSubprocess(config)
    
    with patch.dict(os.environ, {'SAFE_VAR': 'safe', 'DANGEROUS_VAR': 'danger'}):
      with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout='test', stderr='')
        secure_subprocess.run(['env'])
        
        # Check that only whitelisted environment variables are passed
        call_args = mock_run.call_args
        env = call_args[1]['env']
        assert 'SAFE_VAR' in env
        assert 'DANGEROUS_VAR' not in env

class TestPreconfiguredSubprocesses:
  """Test pre-configured subprocess instances."""
  
  def test_knowledgebase_subprocess_config(self):
    """Test that knowledgebase subprocess has correct configuration."""
    subprocess_instance = get_knowledgebase_subprocess()
    
    assert 'customkb' in subprocess_instance.config.allowed_commands
    assert subprocess_instance.config.max_args == 6
    assert subprocess_instance.config.timeout == 300.0
    assert 'ANTHROPIC_API_KEY' in subprocess_instance.config.environment_whitelist
    assert 'OPENAI_API_KEY' in subprocess_instance.config.environment_whitelist
    assert 'GOOGLE_API_KEY' in subprocess_instance.config.environment_whitelist
  
  def test_editor_subprocess_config(self):
    """Test that editor subprocess has correct configuration."""
    subprocess_instance = get_editor_subprocess()
    
    expected_editors = ['nano', 'vim', 'vi', 'emacs', 'joe', 'mcedit', 'micro', 'ne', 'jed', 'gedit']
    for editor in expected_editors:
      assert editor in subprocess_instance.config.allowed_commands
    
    assert subprocess_instance.config.max_args == 5
    assert subprocess_instance.config.timeout == 300.0
    assert 'TERM' in subprocess_instance.config.environment_whitelist
    assert 'EDITOR' in subprocess_instance.config.environment_whitelist

class TestShellEscaping:
  """Test shell escaping functionality."""
  
  def test_shell_escaping(self):
    """Test that shell escaping works correctly."""
    import shlex
    test_cases = [
      ("simple", "simple"),  # shlex.quote doesn't add quotes for simple strings
      ("with spaces", "'with spaces'"),
      ("with'quotes", "'with'\"'\"'quotes'"),
      ("with$special", "'with$special'"),
      ("", "''"),
    ]
    
    for input_text, expected in test_cases:
      result = escape_for_shell(input_text)
      # Verify the result matches expected or is equivalent
      assert result == expected or shlex.quote(input_text) == result

class TestIntegration:
  """Integration tests combining multiple security components."""
  
  def test_secure_knowledgebase_query_flow(self, tmp_path):
    """Test complete secure knowledgebase query flow."""
    # Create mock customkb executable
    customkb_path = tmp_path / "customkb"
    customkb_path.write_text("#!/bin/bash\necho 'mock result'")
    customkb_path.chmod(0o755)
    
    # Create mock knowledgebase file
    kb_path = tmp_path / "test.cfg"
    kb_path.write_text("mock knowledgebase")
    
    # Test with valid inputs
    from context import get_knowledgebase_string
    
    with patch('security.get_knowledgebase_subprocess') as mock_get_subprocess:
      mock_subprocess = MagicMock()
      mock_subprocess.run.return_value = MagicMock(stdout="mock result")
      mock_get_subprocess.return_value = mock_subprocess
      
      result = get_knowledgebase_string(
        str(kb_path),
        "test query",
        str(customkb_path),
        str(tmp_path),
        {}
      )
      
      assert "mock result" in result
      assert "<knowledgebase>" in result
  
  def test_secure_editor_flow(self, tmp_path):
    """Test complete secure editor flow."""
    # Create mock editor
    editor_path = tmp_path / "test_editor"
    editor_path.write_text("#!/bin/bash\necho 'editor executed'")
    editor_path.chmod(0o755)
    
    # Create test file to edit
    test_file = tmp_path / "test.yaml"
    test_file.write_text("test: value\n")
    
    from config import edit_yaml_file
    
    with patch.dict(os.environ, {'EDITOR': str(editor_path)}):
      with patch('config.get_editor_subprocess') as mock_get_subprocess:
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock()
        mock_get_subprocess.return_value = mock_subprocess
        
        # Mock the YAML validation to pass
        with patch('yaml.safe_load'):
          with patch('click.echo'):
            with patch('shutil.move'):  # Don't actually move files
              edit_yaml_file(str(test_file))
        
        # Verify secure subprocess was used
        mock_subprocess.run.assert_called()

if __name__ == '__main__':
  pytest.main([__file__])

#fin