"""
Unit tests for configuration handling in dejavu2-cli.
"""
import os
import pytest
import tempfile
import yaml
import json
from unittest.mock import patch, mock_open, MagicMock

# Import functions from the application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import load_config

class TestConfig:
    """Test configuration loading functionality."""

    def test_load_config_merges_configs(self):
        """Test that load_config properly merges default and user configs."""
        default_config = {
            'defaults': {
                'model': 'claude-3-5-sonnet',
                'temperature': 0.1,
                'max_tokens': 1000
            },
            'paths': {
                'template_path': '/default/path'
            }
        }
        
        user_config = {
            'defaults': {
                'model': 'gpt-4o',  # Override model
                'temperature': 0.7  # Override temperature
            },
            'custom_setting': 'value'  # Add new setting
        }
        
        default_yaml = yaml.dump(default_config)
        user_yaml = yaml.dump(user_config)
        
        # Create a mock for the open function that returns different content for different paths
        def mock_file_open(filename, *args, **kwargs):
            if 'default_config_path' in str(filename):
                return mock_open(read_data=default_yaml)()
            elif 'user_config_path' in str(filename):
                return mock_open(read_data=user_yaml)()
            return mock_open()()
        
        # Mock both files existing
        with patch('builtins.open', side_effect=mock_file_open):
            with patch('os.path.exists', return_value=True):
                config = load_config('default_config_path', 'user_config_path')
                
                # Check merged values
                assert config['defaults']['model'] == 'gpt-4o'  # From user config
                assert config['defaults']['temperature'] == 0.7  # From user config
                assert config['defaults']['max_tokens'] == 1000  # From default config
                assert config['paths']['template_path'] == '/default/path'  # From default config
                assert config['custom_setting'] == 'value'  # Added from user config