"""
Tests for knowledge base integration in dejavu2-cli.
"""
import os
import pytest
import subprocess
from unittest.mock import patch, MagicMock

# Import the knowledge base function from dejavu2_cli.py
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dejavu2_cli import get_knowledgebase_string

# Skip if knowledgebase path is not configured or customkb not installed
kb_available = pytest.mark.skipif(
    not os.path.exists(os.path.join(os.environ.get('VECTORDBS', '/var/lib/vectordbs'), 'okusi/okusiassociates.cfg')), 
    reason="okusiassociates.cfg knowledge base not available"
)

class TestKnowledgeBase:
    """Test interactions with knowledge bases."""
    
    @kb_available
    def test_kb_query(self):
        """Test querying the okusiassociates knowledgebase."""
        result = get_knowledgebase_string(
            knowledgebase="okusiassociates",
            knowledgebase_query="What services does the company offer?"
        )
        
        # Check that we got a proper response
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "<knowledgebase>" in result
        assert "</knowledgebase>" in result
    
    @patch('subprocess.run')
    def test_kb_query_mocked(self, mock_run):
        """Test knowledge base query with a mocked subprocess call."""
        # Set up mock response
        mock_process = MagicMock()
        mock_process.stdout = "Okusi Associates offers software development and consulting services."
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Call the function
        result = get_knowledgebase_string(
            knowledgebase="okusiassociates",
            knowledgebase_query="What services does the company offer?"
        )
        
        # Verify the result
        assert "<knowledgebase>" in result
        assert "Okusi Associates offers software development" in result
        assert "</knowledgebase>" in result
        
        # Verify subprocess call
        mock_run.assert_called_once()