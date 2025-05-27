"""
Unit tests for template handling in dejavu2-cli.
"""
import os
import pytest
import json
from unittest.mock import patch, mock_open, MagicMock

# Import functions from the application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from templates import load_template_data, get_template, list_template_names, list_templates
from errors import ConfigurationError, TemplateError

class TestTemplates:
    """Test template handling functionality."""
    
    def test_load_template_data(self):
        """Test loading template data from a mock JSON file."""
        mock_templates = {
            "Template 1": {
                "category": "General",
                "systemprompt": "You are a helpful assistant.",
                "model": "gpt-4o",
                "temperature": 0.7
            },
            "Template 2": {
                "category": "Code",
                "systemprompt": "You are a code assistant.",
                "model": "claude-3-5-sonnet",
                "temperature": 0.1
            }
        }
        
        mock_json = json.dumps(mock_templates)
        
        with patch('builtins.open', mock_open(read_data=mock_json)):
            with patch('os.path.exists', return_value=True):
                templates = load_template_data('dummy_path.json')
                
                assert "Template 1" in templates
                assert "Template 2" in templates
                assert templates["Template 1"]["category"] == "General"
                assert templates["Template 2"]["model"] == "claude-3-5-sonnet"
    
    def test_load_template_data_file_not_found(self):
        """Test loading templates when the JSON file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ConfigurationError):
                load_template_data('nonexistent.json')
    
    def test_load_template_data_invalid_json(self):
        """Test loading templates with invalid JSON content."""
        with patch('builtins.open', mock_open(read_data='{"invalid": json')):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(TemplateError):
                    load_template_data('invalid.json')
    
    def test_get_template_exact_match(self):
        """Test getting a template with an exact name match."""
        mock_templates = {
            "Template 1": {
                "category": "General",
                "systemprompt": "You are a helpful assistant.",
                "model": "gpt-4o"
            },
            "Template 2": {
                "category": "Code",
                "systemprompt": "You are a code assistant.",
                "model": "claude-3-5-sonnet"
            }
        }
        
        with patch('templates.load_template_data', return_value=mock_templates):
            result = get_template("Template 1", 'dummy_path.json')
            
            assert result is not None
            key, template = result
            assert key == "Template 1"
            assert template["category"] == "General"
            assert template["model"] == "gpt-4o"
    
    def test_get_template_substring_match(self):
        """Test getting a template with a substring match."""
        mock_templates = {
            "Template Alpha": {
                "category": "General",
                "model": "gpt-4o"
            },
            "Template Beta": {
                "category": "Code",
                "model": "claude-3-5-sonnet"
            }
        }
        
        with patch('templates.load_template_data', return_value=mock_templates):
            result = get_template("Alpha", 'dummy_path.json')
            
            assert result is not None
            key, template = result
            assert key == "Template Alpha"
            assert template["category"] == "General"
    
    def test_get_template_not_found(self):
        """Test getting a template that doesn't exist."""
        mock_templates = {
            "Template 1": {
                "category": "General"
            }
        }
        
        with patch('templates.load_template_data', return_value=mock_templates):
            with pytest.raises(TemplateError):
                get_template("NonExistent", 'dummy_path.json')
    
    def test_list_template_names(self):
        """Test listing template names."""
        mock_templates = {
            "Template 1": {"category": "General"},
            "Template 2": {"category": "Code"}
        }
        
        with patch('templates.load_template_data', return_value=mock_templates):
            with patch('sys.stdout.write') as mock_write:
                list_template_names('dummy_path.json')
                # Should have called write with template names
                assert mock_write.called
    
    def test_list_templates_all(self):
        """Test listing all templates."""
        mock_templates = {
            "Template 1": {
                "category": "General",
                "systemprompt": "You are helpful"
            }
        }
        
        with patch('templates.load_template_data', return_value=mock_templates):
            with patch('sys.stdout.write') as mock_write:
                list_templates('dummy_path.json', 'all')
                # Should have called write with template details
                assert mock_write.called
    
    def test_list_templates_specific(self):
        """Test listing a specific template."""
        mock_templates = {
            "Template 1": {
                "category": "General",
                "systemprompt": "You are helpful"
            }
        }
        
        with patch('templates.load_template_data', return_value=mock_templates):
            with patch('sys.stdout.write') as mock_write:
                list_templates('dummy_path.json', 'Template 1')
                # Should have called write with specific template details
                assert mock_write.called

#fin