"""
Unit tests for model handling in dejavu2-cli.
"""
import os
import pytest
import json
from unittest.mock import patch, mock_open, MagicMock

# Import functions from the application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models import list_available_canonical_models, get_canonical_model

class TestModels:
    """Test model handling and selection functionality."""
    
    def test_list_available_canonical_models(self):
        """Test listing available models from a mock JSON file."""
        mock_models = {
            "gpt-4o": {
                "provider": "openai",
                "description": "GPT-4o model from OpenAI"
            },
            "claude-3-5-sonnet": {
                "provider": "anthropic",
                "description": "Claude 3.5 Sonnet from Anthropic"
            }
        }
        
        mock_json = json.dumps(mock_models)
        
        with patch('builtins.open', mock_open(read_data=mock_json)):
            with patch('os.path.exists', return_value=True):
                models = list_available_canonical_models('dummy_path.json')
                
                # Check models list
                assert "gpt-4o" in models
                assert "claude-3-5-sonnet" in models
                assert len(models) == 2
                
    def test_list_available_canonical_models_file_not_found(self):
        """Test listing models when the JSON file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            models = list_available_canonical_models('nonexistent.json')
            assert models == []
    
    def test_list_available_canonical_models_invalid_json(self):
        """Test listing models with invalid JSON content."""
        with patch('builtins.open', mock_open(read_data='{"invalid": json')):
            models = list_available_canonical_models('invalid.json')
            assert models == []
    
    def test_get_canonical_model_exact_match(self):
        """Test getting canonical model with an exact match."""
        mock_models = {
            "gpt-4o": {
                "provider": "openai",
                "description": "GPT-4o model from OpenAI"
            },
            "claude-3-5-sonnet": {
                "provider": "anthropic",
                "description": "Claude 3.5 Sonnet from Anthropic"
            }
        }
        
        mock_json = json.dumps(mock_models)
        
        with patch('builtins.open', mock_open(read_data=mock_json)):
            with patch('os.path.exists', return_value=True):
                model_info = get_canonical_model('gpt-4o', 'dummy_path.json')
                
                assert model_info is not None
                assert model_info["provider"] == "openai"
                assert model_info["description"] == "GPT-4o model from OpenAI"
    
    def test_get_canonical_model_alias(self):
        """Test getting canonical model with an alias."""
        mock_models = {
            "gpt-4o": {
                "provider": "openai",
                "description": "GPT-4o model from OpenAI",
                "aliases": ["gpt4o", "4o"]
            }
        }
        
        mock_json = json.dumps(mock_models)
        
        with patch('builtins.open', mock_open(read_data=mock_json)):
            with patch('os.path.exists', return_value=True):
                model_info = get_canonical_model('4o', 'dummy_path.json')
                
                assert model_info is not None
                assert model_info["canonical_name"] == "gpt-4o"
                assert model_info["provider"] == "openai"
    
    def test_get_canonical_model_not_found(self):
        """Test getting a canonical model that doesn't exist."""
        mock_models = {
            "gpt-4o": {
                "provider": "openai"
            }
        }
        
        mock_json = json.dumps(mock_models)
        
        with patch('builtins.open', mock_open(read_data=mock_json)):
            with patch('os.path.exists', return_value=True):
                model_info = get_canonical_model('nonexistent-model', 'dummy_path.json')
                
                assert model_info is None