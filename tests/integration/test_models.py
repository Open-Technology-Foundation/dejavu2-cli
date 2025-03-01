"""
Tests for model API interactions in dejavu2-cli.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

# Import the query functions from llm_clients.py
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from llm_clients import query_openai, query_anthropic, query

# Skip tests if API keys are not available
require_openai = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"), 
    reason="OpenAI API key not available"
)

require_anthropic = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"), 
    reason="Anthropic API key not available"
)

class TestModelIntegration:
    """Integration tests for model API interactions."""
    
    @require_openai
    def test_openai_query_gpt4o(self):
        """Test a basic query to OpenAI GPT-4o API."""
        result = query_openai(
            query="What is the capital of France?",
            system="You are a helpful assistant that provides short answers.",
            model="gpt-4o",
            temperature=0.1,
            max_tokens=100
        )
        
        # Check the result looks reasonable
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Paris" in result
    
    @pytest.mark.skip(reason="Actual API key is present but unauthorized")
    @require_anthropic
    def test_anthropic_query_sonnet(self):
        """Test a basic query to Anthropic Claude Sonnet API."""
        result = query_anthropic(
            query_text="What is the capital of France?",
            systemprompt="You are a helpful assistant that provides short answers.",
            model="claude-3-5-sonnet-latest",  # Use the latest alias
            temperature=0.1,
            max_tokens=100
        )
        
        # Check the result looks reasonable
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Paris" in result

    @patch('openai.OpenAI')
    def test_openai_query_mocked(self, mock_openai):
        """Test OpenAI query with mocked API (no real API call)."""
        # Set up the mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "The capital of France is Paris."
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the function
        result = query_openai(
            query="What is the capital of France?",
            system="You are a helpful assistant.",
            model="gpt-4o",
            temperature=0.1,
            max_tokens=100
        )
        
        # Verify the result
        assert "Paris" in result
    
    @patch('anthropic.Anthropic')
    def test_anthropic_query_mocked(self, mock_anthropic):
        """Test Anthropic query with mocked API (no real API call)."""
        # Set up the mock response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = "The capital of France is Paris."
        mock_client.messages.create.return_value = mock_message
        
        # Call the function
        result = query_anthropic(
            query_text="What is the capital of France?",
            systemprompt="You are a helpful assistant.",
            model="claude-3-5-sonnet",
            temperature=0.1,
            max_tokens=100
        )
        
        # Verify the result
        assert "Paris" in result
    
    @patch('llm_clients.query_openai')
    @patch('llm_clients.query_anthropic')
    def test_query_router(self, mock_anthropic_query, mock_openai_query):
        """Test that the query router directs to the right provider."""
        # Setup mock responses
        mock_openai_query.return_value = "OpenAI response: Paris"
        mock_anthropic_query.return_value = "Anthropic response: Paris"
        
        # Test routing to OpenAI
        openai_result = query(
            provider="openai",
            query="What is the capital of France?",
            system="You are a helpful assistant.",
            model="gpt-4o",
            temperature=0.1,
            max_tokens=100
        )
        
        # Test routing to Anthropic
        anthropic_result = query(
            provider="anthropic",
            query="What is the capital of France?",
            system="You are a helpful assistant.",
            model="claude-3-5-sonnet",
            temperature=0.1,
            max_tokens=100
        )
        
        # Verify correct routing
        assert "OpenAI response" in openai_result
        assert "Anthropic response" in anthropic_result
        
        # Verify the correct parameters were passed
        mock_openai_query.assert_called_with(
            query="What is the capital of France?",
            system="You are a helpful assistant.",
            model="gpt-4o",
            temperature=0.1,
            max_tokens=100
        )
        
        mock_anthropic_query.assert_called_with(
            query_text="What is the capital of France?",
            systemprompt="You are a helpful assistant.",
            model="claude-3-5-sonnet",
            temperature=0.1,
            max_tokens=100
        )