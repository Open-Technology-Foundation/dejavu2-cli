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
    _query_openai_responses,
    _query_openai_chat_completions
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
    def test_query_openai_chat_completions(self, mock_openai_class):
        """Test OpenAI Chat Completions API (fallback)."""
        # Setup mock client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response from GPT-4"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with use_responses_api=False to force Chat Completions
        result = query_openai(
            client=mock_client,
            query="Test query",
            system="You are helpful",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000,
            conversation_messages=[],
            use_responses_api=False
        )
        
        assert result == "Test response from GPT-4"
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify correct parameters were passed
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o'
        assert call_args[1]['temperature'] == 0.7
        assert 'max_completion_tokens' in call_args[1]
    
    @patch('llm_clients.OpenAI')  
    def test_query_openai_responses_api_fallback(self, mock_openai_class):
        """Test OpenAI Responses API with fallback to Chat Completions."""
        # Setup mock client without responses attribute (fallback scenario)
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        del mock_client.responses  # Remove responses attribute to trigger fallback
        
        # Setup Chat Completions response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Fallback response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with use_responses_api=True (default)
        result = query_openai(
            client=mock_client,
            query="Test query",
            system="You are helpful", 
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert result == "Fallback response"
        # Should fall back to chat completions
        mock_client.chat.completions.create.assert_called_once()

    @patch('llm_clients.OpenAI')
    def test_query_openai_responses_api_success(self, mock_openai_class):
        """Test OpenAI Responses API success path."""
        # Setup mock client with responses attribute
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Setup Responses API response
        mock_response = MagicMock()
        mock_response.output = "Response from Responses API"
        mock_client.responses.create.return_value = mock_response
        
        result = query_openai(
            client=mock_client,
            query="Test query",
            system="You are helpful",
            model="gpt-4o", 
            temperature=0.7,
            max_tokens=1000,
            use_responses_api=True
        )
        
        assert result == "Response from Responses API"
        mock_client.responses.create.assert_called_once()
        
        # Verify Responses API parameters
        call_args = mock_client.responses.create.call_args
        assert call_args[1]['model'] == 'gpt-4o'
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_output_tokens'] == 1000

    def test_openai_o_series_models(self):
        """Test special handling for O-series models (O1, O3, O4)."""
        with patch('llm_clients.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "O-series response"
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test O1 model - should set temperature to 1
            result = query_openai(
                client=mock_client,
                query="Test query",
                system="You are helpful",
                model="o1-preview",
                temperature=0.7,  # Should be overridden to 1
                max_tokens=1000,
                use_responses_api=False
            )
            
            assert result == "O-series response"
            # Check that temperature was set to 1 for O-series models
            call_args = mock_client.chat.completions.create.call_args
            # Note: O-series handling is done in the routing layer, not in query_openai directly

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
            # Verify Responses API is enabled by default
            call_args = mock_query_openai.call_args
            assert call_args[1]['use_responses_api'] == True

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
            
            # Simulate authentication error
            from errors import AuthenticationError
            mock_client.chat.completions.create.side_effect = Exception("invalid_api_key")
            
            with pytest.raises(AuthenticationError):
                query_openai(
                    client=mock_client,
                    query="Test",
                    system="Test",
                    model="gpt-4o",
                    temperature=0.7,
                    max_tokens=100,
                    use_responses_api=False
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