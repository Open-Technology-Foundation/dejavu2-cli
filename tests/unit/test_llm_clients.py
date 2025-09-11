"""
Unit tests for LLM client functionality in dejavu2-cli.

Tests all enabled LLM providers: OpenAI, Anthropic, Google/Gemini, and Ollama.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, Mock
import json
import requests

# Import functions from the application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from llm_clients import (
    get_api_keys, 
    initialize_clients, 
    query_openai, 
    query_anthropic, 
    query_gemini, 
    query_llama,
    query,
    format_messages_for_responses_api,
    _extract_content_from_response,
    _is_reasoning_model,
    _supports_web_search,
    _supports_vision,
    _supports_image_generation
)

class TestLLMClients:
    """Test LLM client functionality for all enabled providers."""
    
    def test_get_api_keys(self):
        """Test getting API keys from environment."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key',
            'GOOGLE_API_KEY': 'test-google-key',
            'OLLAMA_API_KEY': 'test-ollama-key'
        }):
            keys = get_api_keys()
            
            assert keys['OPENAI_API_KEY'] == 'test-openai-key'
            assert keys['ANTHROPIC_API_KEY'] == 'test-anthropic-key'
            assert keys['GOOGLE_API_KEY'] == 'test-google-key'
            assert keys['OLLAMA_API_KEY'] == 'test-ollama-key'
    
    def test_get_api_keys_missing(self):
        """Test getting API keys when some are missing."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key'
        }, clear=True):
            keys = get_api_keys()
            
            assert keys['OPENAI_API_KEY'] == 'test-openai-key'
            assert keys['ANTHROPIC_API_KEY'] == ''
            assert keys['GOOGLE_API_KEY'] == ''
            assert keys['OLLAMA_API_KEY'] == 'llama'  # Default value
    
    def test_initialize_clients(self):
        """Test initializing all LLM clients."""
        api_keys = {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key',
            'GOOGLE_API_KEY': 'test-google-key',
            'OLLAMA_API_KEY': 'test-ollama-key'
        }
        
        with patch('llm_clients.OpenAI') as mock_openai:
            with patch('llm_clients.Anthropic') as mock_anthropic:
                with patch('llm_clients.genai') as mock_genai:
                    clients = initialize_clients(api_keys)
                    
                    # Test all enabled LLM families are initialized
                    assert 'openai' in clients
                    assert 'anthropic' in clients  
                    assert 'google' in clients
                    assert 'ollama' in clients
                    assert 'ollama_local' in clients
                    
                    # Verify correct client initialization calls
                    assert mock_openai.call_count >= 2  # OpenAI + Ollama clients
                    mock_anthropic.assert_called_once_with(api_key='test-anthropic-key')

class TestOpenAIProvider:
    """Test OpenAI family LLMs (GPT-4, ChatGPT, O-series)."""
    
    @patch('llm_clients.OpenAI')
    def test_query_openai_responses_api(self, mock_openai_class):
        """Test OpenAI Responses API."""
        # Setup mock client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Setup mock response with proper Responses API format
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": "Test response from GPT-4"
                }]
            }]
        }
        mock_client.responses.create.return_value = mock_response
        
        # Test with Responses API
        result = query_openai(
            client=mock_client,
            query="Test query",
            system="You are helpful",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000,
            conversation_messages=[]
        )
        
        assert result == "Test response from GPT-4"
        mock_client.responses.create.assert_called_once()
        
        # Verify correct parameters were passed
        call_args = mock_client.responses.create.call_args
        assert call_args[1]['model'] == 'gpt-4o'
        assert call_args[1]['max_output_tokens'] == 1000
        assert 'input' in call_args[1]
    
    def test_format_messages_for_responses_api(self):
        """Test message formatting for Responses API."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        formatted = format_messages_for_responses_api(messages)
        
        # Check system -> developer mapping
        assert formatted[0]["role"] == "developer"
        assert formatted[0]["content"][0]["type"] == "input_text"
        assert formatted[0]["content"][0]["text"] == "You are helpful"
        
        # Check user messages
        assert formatted[1]["role"] == "user"
        assert formatted[1]["content"][0]["type"] == "input_text"
        
        # Check assistant messages use output_text
        assert formatted[2]["role"] == "assistant"
        assert formatted[2]["content"][0]["type"] == "output_text"

    def test_extract_content_from_response(self):
        """Test content extraction from Responses API response."""
        # Test proper Responses API format
        response_data = {
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": "Extracted text"
                }]
            }]
        }
        
        content = _extract_content_from_response(response_data)
        assert content == "Extracted text"
        
        # Test empty response
        assert _extract_content_from_response({}) == ""
        assert _extract_content_from_response(None) == ""

    def test_model_capability_detection(self):
        """Test model capability detection functions."""
        # Test reasoning model detection
        assert _is_reasoning_model("gpt-5") == True
        assert _is_reasoning_model("o1") == True
        assert _is_reasoning_model("o3-mini") == True
        assert _is_reasoning_model("o4-mini") == True
        assert _is_reasoning_model("gpt-5-chat-latest") == False
        assert _is_reasoning_model("gpt-4o") == False
        
        # Test web search support
        assert _supports_web_search("gpt-5") == True
        assert _supports_web_search("o1") == True
        assert _supports_web_search("gpt-5-chat-latest") == False
        
        # Test vision support
        assert _supports_vision("gpt-5") == True
        assert _supports_vision("gpt-4o") == True
        assert _supports_vision("o4") == True
        assert _supports_vision("gpt-4.1-nano") == False
        
        # Test image generation support
        assert _supports_image_generation("gpt-5") == True
        assert _supports_image_generation("o3") == True
        assert _supports_image_generation("gpt-5-nano") == False

class TestAnthropicProvider:
    """Test Anthropic family LLMs (Claude models)."""
    
    @patch('llm_clients.Anthropic')
    def test_query_anthropic_success(self, mock_anthropic_class):
        """Test successful Anthropic Claude query."""
        # Setup mock client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Claude response"
        mock_client.messages.create.return_value = mock_response
        
        result = query_anthropic(
            client=mock_client,
            query_text="Test query",
            systemprompt="You are helpful Claude",
            model="claude-3-5-sonnet-latest",
            temperature=0.7,
            max_tokens=1000,
            conversation_messages=[]
        )
        
        assert result == "Claude response"
        mock_client.messages.create.assert_called_once()
        
        # Verify correct parameters
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['model'] == 'claude-3-5-sonnet-latest'
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 1000
        assert call_args[1]['system'] == 'You are helpful Claude'

    @patch('llm_clients.Anthropic')
    def test_query_anthropic_claude_37_features(self, mock_anthropic_class):
        """Test Claude 3.7 with 2025 features."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Claude 3.7 response with thinking"
        mock_client.messages.create.return_value = mock_response
        
        result = query_anthropic(
            client=mock_client,
            query_text="Complex reasoning task",
            systemprompt="You are helpful",
            model="claude-3-7-sonnet-20250219",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert result == "Claude 3.7 response with thinking"
        
        # Verify 2025 features in extra_headers
        call_args = mock_client.messages.create.call_args
        extra_headers = call_args[1]['extra_headers']
        assert 'interleaved-thinking-2025-05-14' in extra_headers['anthropic-beta']
        assert 'token-efficient-tools-2025-02-19' in extra_headers['anthropic-beta']

class TestGoogleGeminiProvider:
    """Test Google/Gemini family LLMs."""
    
    @patch('multiprocessing.get_context')
    def test_query_gemini_success(self, mock_get_context):
        """Test successful Google Gemini query."""
        # Setup mock multiprocessing
        mock_ctx = MagicMock()
        mock_pool = MagicMock()
        mock_pool.apply.return_value = "Gemini response"
        mock_ctx.Pool.return_value.__enter__ = MagicMock(return_value=mock_pool)
        mock_ctx.Pool.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_context.return_value = mock_ctx
        
        result = query_gemini(
            query="Test query",
            system="You are helpful Gemini",
            model="gemini-2.0-flash",
            temperature=0.7,
            max_tokens=1000,
            api_key="test-google-key",
            conversation_messages=[]
        )
        
        assert result == "Gemini response"
        mock_pool.apply.assert_called_once()
    
    @patch('multiprocessing.get_context')
    def test_query_gemini_2025_features(self, mock_get_context):
        """Test Gemini with 2025 optimizations."""
        mock_ctx = MagicMock()
        mock_pool = MagicMock()
        mock_pool.apply.return_value = "Gemini 2.5 response"
        mock_ctx.Pool.return_value.__enter__ = MagicMock(return_value=mock_pool)
        mock_ctx.Pool.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_context.return_value = mock_ctx
        
        result = query_gemini(
            query="Test query",
            system="You are helpful",
            model="gemini-2.5-pro-exp-03-25",
            temperature=0.8,  # Should use top_p=0.95 optimization
            max_tokens=2000,
            api_key="test-google-key"
        )
        
        assert result == "Gemini 2.5 response"

class TestOllamaProvider:
    """Test Ollama family LLMs (Llama, Gemma, etc.)."""
    
    @patch('llm_clients.requests')
    def test_query_llama_local_success(self, mock_requests):
        """Test successful local Ollama/Llama query."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.base_url = "http://localhost:11434/v1"
        
        # Setup mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"message": {"content": "Llama response"}, "done": true}'
        mock_requests.post.return_value = mock_response
        
        result = query_llama(
            client=mock_client,
            query_text="Test query",
            systemprompt="You are helpful Llama",
            model="gemma3:4b",
            temperature=0.7,
            max_tokens=1000,
            conversation_messages=[],
            api_keys={'OLLAMA_API_KEY': 'ollama'}
        )
        
        assert result == "Llama response"
        mock_requests.post.assert_called_once()
        
        # Verify request parameters
        call_args = mock_requests.post.call_args
        assert 'http://localhost:11434/api/chat' in call_args[0][0]
        request_data = call_args[1]['json']
        assert request_data['model'] == 'gemma3:4b'
        assert request_data['temperature'] == 0.7
        assert request_data['max_tokens'] == 1000

    @patch('llm_clients.requests')
    def test_query_llama_remote_success(self, mock_requests):
        """Test successful remote Ollama query."""
        # Setup mock client for remote
        mock_client = MagicMock()
        mock_client.base_url = "https://ai.okusi.id/api/v1"
        
        # Setup mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"message": {"content": "Remote Llama response"}, "done": true}'
        mock_requests.post.return_value = mock_response
        
        result = query_llama(
            client=mock_client,
            query_text="Test query",
            systemprompt="You are helpful",
            model="gemma3:12b",
            temperature=0.8,
            max_tokens=1500,
            api_keys={'OLLAMA_API_KEY': 'remote-key'}
        )
        
        assert result == "Remote Llama response"
        mock_requests.post.assert_called_once()
        
        # Verify remote URL and auth
        call_args = mock_requests.post.call_args
        assert 'ai.okusi.id' in call_args[0][0]
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer remote-key'

class TestLLMRouting:
    """Test main query routing to all LLM families."""
    
    def test_query_routing_openai_family(self):
        """Test query routing for OpenAI family models."""
        clients = {'openai': MagicMock()}
        api_keys = {'OPENAI_API_KEY': 'test-key'}
        model_parameters = {'family': 'openai', 'max_output_tokens': 4000}
        
        with patch('llm_clients.query_openai') as mock_query_openai:
            mock_query_openai.return_value = "OpenAI response"
            
            result = query(
                clients=clients,
                query_text="Test query",
                systemprompt="You are helpful",
                messages=[],
                model="gpt-4o",
                temperature=0.7,
                max_tokens=1000,
                model_parameters=model_parameters,
                api_keys=api_keys
            )
            
            assert result == "OpenAI response"
            mock_query_openai.assert_called_once()
            # Verify query_openai is called with correct args (no use_responses_api param)
            call_args = mock_query_openai.call_args
            assert 'use_responses_api' not in call_args[1]

    def test_query_routing_anthropic_family(self):
        """Test query routing for Anthropic family models."""
        clients = {'anthropic': MagicMock()}
        api_keys = {'ANTHROPIC_API_KEY': 'test-key'}
        model_parameters = {'family': 'anthropic', 'max_output_tokens': 4000}
        
        with patch('llm_clients.query_anthropic') as mock_query_anthropic:
            mock_query_anthropic.return_value = "Anthropic response"
            
            result = query(
                clients=clients,
                query_text="Test query",
                systemprompt="You are helpful",
                messages=[],
                model="claude-3-5-sonnet-latest",
                temperature=0.7,
                max_tokens=1000,
                model_parameters=model_parameters,
                api_keys=api_keys
            )
            
            assert result == "Anthropic response"
            mock_query_anthropic.assert_called_once()

    def test_query_routing_google_family(self):
        """Test query routing for Google/Gemini family models."""
        clients = {'google': True}
        api_keys = {'GOOGLE_API_KEY': 'test-key'}
        model_parameters = {'family': 'google', 'max_output_tokens': 4000}
        
        with patch('llm_clients.query_gemini') as mock_query_gemini:
            mock_query_gemini.return_value = "Gemini response"
            
            result = query(
                clients=clients,
                query_text="Test query",
                systemprompt="You are helpful",
                messages=[],
                model="gemini-2.0-flash",
                temperature=0.7,
                max_tokens=1000,
                model_parameters=model_parameters,
                api_keys=api_keys
            )
            
            assert result == "Gemini response"
            mock_query_gemini.assert_called_once()

    def test_query_routing_ollama_family(self):
        """Test query routing for Ollama family models."""
        clients = {'ollama': MagicMock(), 'ollama_local': MagicMock()}
        api_keys = {'OLLAMA_API_KEY': 'test-key'}
        model_parameters = {'family': 'ollama', 'max_output_tokens': 4000, 'url': 'http://localhost:11434'}
        
        with patch('llm_clients.query_llama') as mock_query_llama:
            mock_query_llama.return_value = "Llama response"
            
            result = query(
                clients=clients,
                query_text="Test query", 
                systemprompt="You are helpful",
                messages=[],
                model="gemma3:4b",
                temperature=0.7,
                max_tokens=1000,
                model_parameters=model_parameters,
                api_keys=api_keys
            )
            
            assert result == "Llama response"
            mock_query_llama.assert_called_once()

class TestErrorHandling:
    """Test error handling for all LLM providers."""
    
    def test_openai_authentication_error(self):
        """Test OpenAI authentication error handling."""
        with patch('llm_clients.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Simulate authentication error on Responses API
            from errors import AuthenticationError
            mock_client.responses.create.side_effect = Exception("invalid_api_key")
            
            with pytest.raises(AuthenticationError):
                query_openai(
                    client=mock_client,
                    query="Test",
                    system="Test",
                    model="gpt-4o",
                    temperature=0.7,
                    max_tokens=100
                )

    def test_anthropic_rate_limit_error(self):
        """Test Anthropic rate limit error handling."""
        with patch('llm_clients.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_anthropic_class.return_value = mock_client
            
            # Simulate rate limit error
            error = Exception("rate limit")
            error.status_code = 429
            mock_client.messages.create.side_effect = error
            
            from errors import APIError
            with pytest.raises(APIError):
                query_anthropic(
                    client=mock_client,
                    query_text="Test",
                    systemprompt="Test",
                    model="claude-3-5-sonnet-latest",
                    temperature=0.7,
                    max_tokens=100
                )

    def test_unsupported_model_family(self):
        """Test handling of unsupported model families."""
        clients = {}
        api_keys = {}
        model_parameters = {'family': 'unsupported', 'max_output_tokens': 4000}
        
        from errors import ConfigurationError
        with pytest.raises(ConfigurationError):
            query(
                clients=clients,
                query_text="Test query",
                systemprompt="Test",
                messages=[],
                model="unknown-model",
                temperature=0.7,
                max_tokens=1000,
                model_parameters=model_parameters,
                api_keys=api_keys
            )

if __name__ == "__main__":
    pytest.main([__file__])