"""
Unit tests for context handling in dejavu2-cli.
"""

import os

# Import functions from the application
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from context import get_knowledgebase_string, get_reference_string
from errors import KnowledgeBaseError, ReferenceError


class TestContext:
  """Test context and reference handling functionality."""

  def test_get_reference_string_single_file(self):
    """Test getting reference string from a single file."""
    test_content = "This is a reference file.\nIt contains test content."

    with patch("builtins.open", mock_open(read_data=test_content)):
      with patch("context.validate_file_path", return_value="/path/test_file.txt"):
        ref_string = get_reference_string("test_file.txt")

        assert "<reference" in ref_string
        assert "This is a reference file." in ref_string
        assert "It contains test content." in ref_string
        assert "</reference>" in ref_string

  def test_get_reference_string_multiple_files(self):
    """Test getting reference string from multiple files."""
    file_contents = {"/path/file1.txt": "Content of file 1", "/path/file2.txt": "Content of file 2"}

    def mock_file_open(filename, *args, **kwargs):
      if str(filename) in file_contents:
        return mock_open(read_data=file_contents[str(filename)])()
      return mock_open(read_data="default content")()

    def mock_validate_path(path, must_exist=False):
      return f"/path/{path}"

    with patch("builtins.open", side_effect=mock_file_open), patch("context.validate_file_path", side_effect=mock_validate_path):
      ref_string = get_reference_string("file1.txt,file2.txt")

      assert "<reference" in ref_string
      assert "Content of file 1" in ref_string
      assert "Content of file 2" in ref_string
      assert "</reference>" in ref_string

  def test_get_reference_string_file_not_found(self):
    """Test getting reference string when file doesn't exist."""
    with patch("context.validate_file_path", side_effect=FileNotFoundError("File not found")), pytest.raises(ReferenceError):
      get_reference_string("nonexistent.txt")

  def test_get_reference_string_empty_string(self):
    """Test getting reference string with empty string."""
    ref_string = get_reference_string("")

    assert ref_string == ""

  def test_get_reference_string_none(self):
    """Test getting reference string with None input."""
    ref_string = get_reference_string(None)

    assert ref_string == ""

  def test_get_knowledgebase_string(self):
    """Test knowledgebase query function."""
    with patch("context.validate_knowledgebase_query", return_value="safe query"):
      with patch("context.validate_file_path", side_effect=lambda x, must_exist=False: x):
        with patch("os.path.exists", return_value=True):
          with patch("context.get_knowledgebase_subprocess") as mock_subprocess:
            # Mock the subprocess properly with a run method
            mock_proc = MagicMock()
            mock_proc.run.return_value.stdout = "Knowledgebase content about query"
            mock_subprocess.return_value = mock_proc

            result = get_knowledgebase_string(
              knowledgebase="test_kb.cfg",
              knowledgebase_query="test query",
              customkb_executable="/path/to/customkb",
              vectordbs_path="/path/to/vectordbs",
              api_keys={"OPENAI_API_KEY": "test-key"},
            )

            # Verify the result
            assert "<knowledgebase>" in result
            assert "Knowledgebase content about query" in result
            assert "</knowledgebase>" in result

  def test_get_knowledgebase_string_failure(self):
    """Test knowledgebase query function when subprocess fails."""
    with patch("context.validate_knowledgebase_query", return_value="safe query"):
      with patch("context.validate_file_path", side_effect=lambda x, must_exist=False: x):
        with patch("os.path.exists", return_value=True):
          with patch("context.get_knowledgebase_subprocess", side_effect=Exception("KB error")):
            with pytest.raises(KnowledgeBaseError):
              get_knowledgebase_string(
                knowledgebase="test_kb.cfg",
                knowledgebase_query="test query",
                customkb_executable="/path/to/customkb",
                vectordbs_path="/path/to/vectordbs",
                api_keys={"OPENAI_API_KEY": "test-key"},
              )

  # Phase 4A: Coverage improvement tests

  def test_get_reference_string_validation_error(self):
    """Test that ValidationError is properly caught and re-raised as ReferenceError."""
    from security import ValidationError

    with patch("context.validate_file_path") as mock_validate:
      mock_validate.side_effect = ValidationError("Path contains dangerous characters")

      with pytest.raises(ReferenceError, match="Invalid reference file path"):
        get_reference_string("/bad/path;rm")

  def test_get_reference_string_os_error(self):
    """Test that OSError is properly caught and re-raised as ReferenceError."""
    with patch("context.validate_file_path") as mock_validate, patch("builtins.open") as mock_file:
      mock_validate.return_value = "/valid/path.txt"
      mock_file.side_effect = OSError("Permission denied")

      with pytest.raises(ReferenceError, match="Cannot read reference file"):
        get_reference_string("/valid/path.txt")

  def test_get_reference_string_unicode_error(self):
    """Test that UnicodeDecodeError is properly caught and re-raised as ReferenceError."""
    with patch("context.validate_file_path") as mock_validate, patch("builtins.open", mock_open()) as mock_file:
      mock_validate.return_value = "/valid/binary.dat"
      mock_file.return_value.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

      with pytest.raises(ReferenceError, match="Cannot decode reference file"):
        get_reference_string("/valid/binary.dat")

  def test_get_knowledgebase_string_path_search_env(self):
    """Test knowledgebase path search using VECTORDBS environment variable."""
    with patch("context.validate_knowledgebase_query") as mock_validate_query, patch(
      "context.validate_file_path"
    ) as mock_validate_path, patch("os.path.exists") as mock_exists, patch("os.environ.get") as mock_env_get, patch("context.glob") as mock_glob, patch(
      "context.get_knowledgebase_subprocess"
    ) as mock_get_subprocess:
      mock_validate_query.return_value = "test query"
      mock_validate_path.side_effect = lambda path, must_exist=False: path
      mock_exists.return_value = False
      mock_env_get.return_value = "/env/vectordbs"
      mock_glob.side_effect = [["/env/vectordbs/okusi/test.cfg"], []]

      mock_subprocess = MagicMock()
      mock_subprocess.config.environment_whitelist = ["ANTHROPIC_API_KEY"]
      mock_process_result = MagicMock()
      mock_process_result.stdout = "Knowledgebase results"
      mock_subprocess.run.return_value = mock_process_result
      mock_get_subprocess.return_value = mock_subprocess

      result = get_knowledgebase_string("test", "test query", "/usr/bin/customkb", "/var/lib/vectordbs", {})

      assert mock_env_get.called
      assert "<knowledgebase>" in result
      assert "Knowledgebase results" in result

  def test_get_knowledgebase_string_path_search_default(self):
    """Test knowledgebase path search using default vectordbs_path."""
    with patch("context.validate_knowledgebase_query") as mock_validate_query, patch(
      "context.validate_file_path"
    ) as mock_validate_path, patch("os.path.exists") as mock_exists, patch("os.environ.get") as mock_env_get, patch("context.glob") as mock_glob, patch(
      "context.get_knowledgebase_subprocess"
    ) as mock_get_subprocess:
      mock_validate_query.return_value = "test query"
      mock_validate_path.side_effect = lambda path, must_exist=False: path
      mock_exists.return_value = False
      mock_env_get.return_value = "/var/lib/vectordbs"
      mock_glob.side_effect = [[], ["/var/lib/vectordbs/test/test.cfg"]]

      mock_subprocess = MagicMock()
      mock_subprocess.config.environment_whitelist = []
      mock_process_result = MagicMock()
      mock_process_result.stdout = "Results from default path"
      mock_subprocess.run.return_value = mock_process_result
      mock_get_subprocess.return_value = mock_subprocess

      result = get_knowledgebase_string("test", "test query", "/usr/bin/customkb", "/var/lib/vectordbs", {})

      assert "<knowledgebase>" in result
      assert "Results from default path" in result

  def test_get_knowledgebase_string_not_found(self):
    """Test KnowledgeBaseError when knowledgebase file is not found."""
    with patch("context.validate_knowledgebase_query") as mock_validate_query, patch(
      "context.validate_file_path"
    ) as mock_validate_path, patch("os.path.exists") as mock_exists, patch("os.environ.get") as mock_env_get, patch("context.glob") as mock_glob:
      mock_validate_query.return_value = "test query"
      mock_validate_path.side_effect = lambda path, must_exist=False: path
      mock_exists.return_value = False
      mock_env_get.return_value = "/var/lib/vectordbs"
      mock_glob.return_value = []

      with pytest.raises(KnowledgeBaseError, match="not found in"):
        get_knowledgebase_string("nonexistent", "test query", "/usr/bin/customkb", "/var/lib/vectordbs", {})

  def test_get_knowledgebase_string_security_error(self):
    """Test that SecurityError is properly caught and re-raised as KnowledgeBaseError."""
    from security import SecurityError

    with patch("context.validate_knowledgebase_query") as mock_validate_query:
      mock_validate_query.side_effect = SecurityError("Command timed out")

      with pytest.raises(KnowledgeBaseError, match="Security error"):
        get_knowledgebase_string("test", "test query", "/usr/bin/customkb", "/var/lib/vectordbs", {})

  def test_get_knowledgebase_string_subprocess_error(self):
    """Test that subprocess CalledProcessError is caught and re-raised as KnowledgeBaseError."""
    import subprocess

    with patch("context.validate_knowledgebase_query") as mock_validate_query, patch(
      "context.validate_file_path"
    ) as mock_validate_path, patch("os.path.exists") as mock_exists, patch("context.get_knowledgebase_subprocess") as mock_get_subprocess:
      mock_validate_query.return_value = "test query"
      mock_validate_path.side_effect = lambda path, must_exist=False: path
      mock_exists.return_value = True

      mock_subprocess = MagicMock()
      mock_subprocess.config.environment_whitelist = []
      mock_subprocess.run.side_effect = subprocess.CalledProcessError(1, "customkb")
      mock_get_subprocess.return_value = mock_subprocess

      with pytest.raises(KnowledgeBaseError, match="Knowledgebase executable failed"):
        get_knowledgebase_string("test.cfg", "test query", "/usr/bin/customkb", "/var/lib/vectordbs", {})

  def test_list_knowledge_bases_success(self):
    """Test successful listing of knowledgebases."""
    from context import list_knowledge_bases

    with patch("os.path.isdir") as mock_isdir, patch("context.glob") as mock_glob, patch("os.path.realpath") as mock_realpath, patch(
      "click.echo"
    ) as mock_echo:
      mock_isdir.return_value = True
      mock_glob.return_value = ["/var/lib/vectordbs/okusi/test1.cfg", "/var/lib/vectordbs/okusi/test2.cfg", "/var/lib/vectordbs/test3.cfg"]
      mock_realpath.side_effect = lambda x: x

      result = list_knowledge_bases("/var/lib/vectordbs")

      assert len(result) == 3
      assert "/var/lib/vectordbs/okusi/test1.cfg" in result
      assert "/var/lib/vectordbs/okusi/test2.cfg" in result
      assert "/var/lib/vectordbs/test3.cfg" in result
      assert mock_echo.called

  def test_list_knowledge_bases_invalid_dir(self):
    """Test that KnowledgeBaseError is raised when directory is invalid."""
    from context import list_knowledge_bases

    with patch("os.path.isdir") as mock_isdir:
      mock_isdir.return_value = False

      with pytest.raises(KnowledgeBaseError, match="not a valid directory"):
        list_knowledge_bases("/invalid/path")
