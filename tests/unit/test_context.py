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
from errors import ReferenceError, KnowledgeBaseError

class TestContext:
    """Test context and reference handling functionality."""
    
    def test_get_reference_string_single_file(self):
        """Test getting reference string from a single file."""
        test_content = "This is a reference file.\nIt contains test content."
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            with patch('context.validate_file_path', return_value='/path/test_file.txt'):
                ref_string = get_reference_string('test_file.txt')
                
                assert "<reference" in ref_string
                assert "This is a reference file." in ref_string
                assert "It contains test content." in ref_string
                assert "</reference>" in ref_string
    
    def test_get_reference_string_multiple_files(self):
        """Test getting reference string from multiple files."""
        file_contents = {
            '/path/file1.txt': 'Content of file 1',
            '/path/file2.txt': 'Content of file 2'
        }
        
        def mock_file_open(filename, *args, **kwargs):
            if str(filename) in file_contents:
                return mock_open(read_data=file_contents[str(filename)])()
            return mock_open(read_data='default content')()
        
        def mock_validate_path(path, must_exist=False):
            return f'/path/{path}'
        
        with patch('builtins.open', side_effect=mock_file_open):
            with patch('context.validate_file_path', side_effect=mock_validate_path):
                ref_string = get_reference_string('file1.txt,file2.txt')
                
                assert "<reference" in ref_string
                assert "Content of file 1" in ref_string
                assert "Content of file 2" in ref_string
                assert "</reference>" in ref_string
    
    def test_get_reference_string_file_not_found(self):
        """Test getting reference string when file doesn't exist."""
        with patch('context.validate_file_path', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(ReferenceError):
                get_reference_string('nonexistent.txt')
    
    def test_get_reference_string_empty_string(self):
        """Test getting reference string with empty string."""
        ref_string = get_reference_string('')
        
        assert ref_string == ""
    
    def test_get_reference_string_none(self):
        """Test getting reference string with None input."""
        ref_string = get_reference_string(None)
        
        assert ref_string == ""
    
    def test_get_knowledgebase_string(self):
        """Test knowledgebase query function."""
        with patch('context.validate_knowledgebase_query', return_value="safe query"):
            with patch('context.validate_file_path', side_effect=lambda x, must_exist=False: x):
                with patch('os.path.exists', return_value=True):
                    with patch('context.get_knowledgebase_subprocess') as mock_subprocess:
                        # Mock the subprocess properly with a run method
                        mock_proc = MagicMock()
                        mock_proc.run.return_value.stdout = "Knowledgebase content about query"
                        mock_subprocess.return_value = mock_proc
                        
                        result = get_knowledgebase_string(
                            knowledgebase="test_kb.cfg",
                            knowledgebase_query="test query",
                            customkb_executable="/path/to/customkb",
                            vectordbs_path="/path/to/vectordbs",
                            api_keys={"OPENAI_API_KEY": "test-key"}
                        )
                        
                        # Verify the result
                        assert "<knowledgebase>" in result
                        assert "Knowledgebase content about query" in result
                        assert "</knowledgebase>" in result
    
    def test_get_knowledgebase_string_failure(self):
        """Test knowledgebase query function when subprocess fails."""
        with patch('context.validate_knowledgebase_query', return_value="safe query"):
            with patch('context.validate_file_path', side_effect=lambda x, must_exist=False: x):
                with patch('os.path.exists', return_value=True):
                    with patch('context.get_knowledgebase_subprocess', side_effect=Exception("KB error")):
                        with pytest.raises(KnowledgeBaseError):
                            get_knowledgebase_string(
                                knowledgebase="test_kb.cfg", 
                                knowledgebase_query="test query",
                                customkb_executable="/path/to/customkb",
                                vectordbs_path="/path/to/vectordbs",
                                api_keys={"OPENAI_API_KEY": "test-key"}
                            )