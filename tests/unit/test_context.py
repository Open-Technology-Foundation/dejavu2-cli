"""
Unit tests for context handling in dejavu2-cli.
"""
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock, call

# Import functions from the application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from context import get_reference_string, get_knowledgebase_string

class TestContext:
    """Test context and reference handling functionality."""
    
    def test_get_reference_string_single_file(self):
        """Test getting reference string from a single file."""
        test_content = "This is a reference file.\nIt contains test content."
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isfile', return_value=True):
                    ref_string = get_reference_string(['test_file.txt'])
                    
                    assert "<reference>" in ref_string
                    assert "This is a reference file." in ref_string
                    assert "It contains test content." in ref_string
                    assert "</reference>" in ref_string
    
    def test_get_reference_string_multiple_files(self):
        """Test getting reference string from multiple files."""
        file_contents = {
            'file1.txt': 'Content of file 1',
            'file2.txt': 'Content of file 2'
        }
        
        def mock_file_open(filename, *args, **kwargs):
            for file_path, content in file_contents.items():
                if file_path in str(filename):
                    return mock_open(read_data=content)()
            return mock_open()()
        
        with patch('builtins.open', side_effect=mock_file_open):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isfile', return_value=True):
                    ref_string = get_reference_string(['file1.txt', 'file2.txt'])
                    
                    assert "<reference>" in ref_string
                    assert "Content of file 1" in ref_string
                    assert "Content of file 2" in ref_string
                    assert "</reference>" in ref_string
    
    def test_get_reference_string_file_not_found(self):
        """Test getting reference string when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            ref_string = get_reference_string(['nonexistent.txt'])
            
            assert "<reference>" in ref_string
            assert "File not found: nonexistent.txt" in ref_string
            assert "</reference>" in ref_string
    
    def test_get_reference_string_empty_list(self):
        """Test getting reference string with empty file list."""
        ref_string = get_reference_string([])
        
        assert ref_string == ""
    
    def test_get_reference_string_directory(self):
        """Test getting reference string from a directory."""
        directory_files = ['dir/file1.txt', 'dir/file2.txt']
        file_contents = {
            'dir/file1.txt': 'Content of file 1',
            'dir/file2.txt': 'Content of file 2'
        }
        
        def mock_file_open(filename, *args, **kwargs):
            for file_path, content in file_contents.items():
                if file_path in str(filename):
                    return mock_open(read_data=content)()
            return mock_open()()
        
        with patch('builtins.open', side_effect=mock_file_open):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isfile', side_effect=lambda x: x in directory_files):
                    with patch('os.path.isdir', return_value=True):
                        with patch('os.walk', return_value=[('dir', [], ['file1.txt', 'file2.txt'])]):
                            ref_string = get_reference_string(['dir'])
                            
                            assert "<reference>" in ref_string
                            assert "Content of file 1" in ref_string
                            assert "Content of file 2" in ref_string
                            assert "</reference>" in ref_string
    
    @patch('subprocess.run')
    def test_get_knowledgebase_string(self, mock_run):
        """Test knowledge base query function."""
        # Set up mock response
        mock_process = MagicMock()
        mock_process.stdout = "Knowledge base content about query"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Call the function
        result = get_knowledgebase_string(
            knowledgebase="test_kb",
            knowledgebase_query="test query"
        )
        
        # Verify the result
        assert "<knowledgebase>" in result
        assert "Knowledge base content about query" in result
        assert "</knowledgebase>" in result
        
        # Verify subprocess call
        mock_run.assert_called_once()
        # Check that the KB name and query are included in the command
        call_args = mock_run.call_args
        # The first argument should be a list of command parts
        command = call_args[1]['args']
        assert "test_kb" in command
        assert "test query" in command
    
    @patch('subprocess.run')
    def test_get_knowledgebase_string_failure(self, mock_run):
        """Test knowledge base query function when subprocess fails."""
        # Set up mock error response
        mock_process = MagicMock()
        mock_process.stderr = "Error accessing knowledge base"
        mock_process.returncode = 1
        mock_run.return_value = mock_process
        
        # Call the function
        result = get_knowledgebase_string(
            knowledgebase="test_kb",
            knowledgebase_query="test query"
        )
        
        # Verify the result contains the error
        assert "<knowledgebase>" in result
        assert "Error accessing knowledge base" in result
        assert "</knowledgebase>" in result