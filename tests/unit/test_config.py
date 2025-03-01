"""
Unit tests for configuration handling in dejavu2-cli.
"""
import os
import pytest
import tempfile
import yaml
import json
from unittest.mock import patch, mock_open

# Import functions from the application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dejavu2_cli import load_config, load_template_data

class TestConfig:
    """Test configuration loading functionality."""
    
    @pytest.mark.skip(reason="Mock setup needs adjustment for actual config structure")
    def test_load_config_with_mocked_files(self):
        """Test config loading with mocked YAML files."""
        default_config = {
            'defaults': {
                'model': 'sonnet',
                'temperature': 0.1,
                'systemprompt': 'You are a helpful assistant.'
            },
            'paths': {
                'template_path': '/path/to/templates'
            }
        }
        
        user_config = {
            'defaults': {
                'temperature': 0.7  # Override temperature
            }
        }
        
        # Mock the default config file
        default_yaml = yaml.dump(default_config)
        user_yaml = yaml.dump(user_config)
        
        # Create a mocked open that returns different content for different paths
        def mock_file_open(filename, *args, **kwargs):
            if 'defaults.yaml' in filename:
                return mock_open(read_data=default_yaml)()
            elif '.config/dejavu2-cli/config.yaml' in filename:
                return mock_open(read_data=user_yaml)()
            return mock_open()()
        
        with patch('builtins.open', side_effect=mock_file_open):
            with patch('os.path.exists', return_value=True):
                config = load_config()
                
                # Verify merged config
                assert 'defaults' in config
                assert 'paths' in config

    def test_load_template_data(self):
        """Test template data loading."""
        template_data = {
            "Test Template": {
                "category": "General",
                "systemprompt": "You are a test assistant.",
                "model": "gpt-4o",
                "max_tokens": 1000,
                "temperature": 0.5
            }
        }
        
        # Mock the JSON data
        template_json = json.dumps(template_data)
        
        with patch('builtins.open', mock_open(read_data=template_json)):
            with patch('os.path.exists', return_value=True):
                with patch('dejavu2_cli.TEMPLATE_PATH', 'mock_path'):
                    templates = load_template_data()
                    
                    assert "Test Template" in templates
                    assert templates["Test Template"]["category"] == "General"
                    assert templates["Test Template"]["model"] == "gpt-4o"