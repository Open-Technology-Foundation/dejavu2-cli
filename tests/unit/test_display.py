"""
Unit tests for display functions in dejavu2-cli.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import io
import sys

# Import functions from the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from display import display_status

class TestDisplay:
    """Test display formatting and output functions."""
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_display_status(self, mock_stdout):
        """Test displaying status information."""
        config = {
            "defaults": {
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        model_parameters = {
            "family": "openai",
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_tokens": 1000,
            "max_output_tokens": 1000,
            "context_window": 128000,
            "systemprompt": "You are a test assistant."
        }
        
        kwargs = {
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_tokens": 1000,
            "systemprompt": "You are a test assistant.",
            "template": "test_template",
            "reference": ["test.txt"],
            "knowledgebase": "test_kb",
            "knowledgebase_query": "test query"
        }
        
        query_texts = ["Test query"]
        
        # Call display_status
        display_status(
            kwargs=kwargs,
            query_texts=query_texts,
            config=config,
            model_parameters=model_parameters,
            print_full_systemprompt=True,
            conversation=None
        )
        
        # Get the captured output
        output = mock_stdout.getvalue()
        
        # Check that the output contains expected sections
        assert "CONFIGURATION" in output.upper() or "configuration" in output.lower()
        assert "MODEL" in output.upper() or "model" in output.lower()
        
        # Check specific details
        assert "gpt-4o" in output
        assert "openai" in output
        assert "0.5" in output  # Temperature
        assert "You are a test assistant" in output
        assert "test.txt" in output
        assert "test_kb" in output
        assert "test query" in output