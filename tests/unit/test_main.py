"""
Unit tests for main module functionality in dejavu2-cli.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, Mock
from click.testing import CliRunner

# Import functions from the application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import main

class TestMain:
    """Test main CLI functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test that help command works."""
        runner = CliRunner()
        result = runner.invoke(main.main, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
    
    def test_main_version(self):
        """Test version flag."""
        runner = CliRunner()
        result = runner.invoke(main.main, ['--version'])
        assert result.exit_code == 0
        assert 'dejavu2-cli' in result.output
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    @patch('main.get_canonical_model')
    @patch('main.get_api_keys')
    @patch('main.initialize_clients')
    @patch('main.query')
    def test_main_simple_query(self, mock_query, mock_init_clients, mock_get_keys, 
                              mock_get_model, mock_conv_manager, mock_load_config):
        """Test a simple query execution."""
        # Setup mocks
        mock_load_config.return_value = {
            'defaults': {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 1000,
                'template': None
            },
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        mock_conv_manager_instance.new_conversation.return_value = MagicMock()
        
        mock_get_model.return_value = ('gpt-4o', {
            'model': 'gpt-4o',
            'parent': 'openai',
            'apikey': 'OPENAI_API_KEY',
            'api_key_valid': True
        })
        
        mock_get_keys.return_value = {'OPENAI_API_KEY': 'test-key'}
        mock_init_clients.return_value = {'openai': MagicMock()}
        mock_query.return_value = "Test response"
        
        runner = CliRunner()
        result = runner.invoke(main.main, ['Test query'])
        
        assert result.exit_code == 0
        assert mock_query.called
    
    @patch('main.load_config')
    @patch('main.list_models')
    def test_main_list_models(self, mock_list_models, mock_load_config):
        """Test listing models."""
        mock_load_config.return_value = {
            'defaults': {'model': 'gpt-4o'},
            'paths': {'template_path': 'Agents.json'}
        }
        
        runner = CliRunner()
        result = runner.invoke(main.main, ['--list-models'])
        
        assert result.exit_code == 0
        mock_list_models.assert_called_once()
    
    @patch('main.load_config')
    @patch('main.list_templates')
    def test_main_list_templates(self, mock_list_templates, mock_load_config):
        """Test listing templates."""
        mock_load_config.return_value = {
            'defaults': {'model': 'gpt-4o'},
            'paths': {'template_path': 'Agents.json'}
        }
        
        runner = CliRunner()
        result = runner.invoke(main.main, ['--list-template', 'all'])
        
        assert result.exit_code == 0
        mock_list_templates.assert_called_once_with(
            os.path.join(main.PRGDIR, 'Agents.json'), 'all'
        )
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    def test_main_list_conversations(self, mock_conv_manager, mock_load_config):
        """Test listing conversations."""
        mock_load_config.return_value = {
            'defaults': {'model': 'gpt-4o'},
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        mock_conv_manager_instance.list_conversations.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(main.main, ['--list-conversations'])
        
        assert result.exit_code == 0
        assert "No saved conversations found." in result.output
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    def test_main_delete_conversation(self, mock_conv_manager, mock_load_config):
        """Test deleting a conversation."""
        mock_load_config.return_value = {
            'defaults': {'model': 'gpt-4o'},
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        mock_conv_manager_instance.delete_conversation.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(main.main, ['--delete-conversation', 'test-id'])
        
        assert result.exit_code == 0
        assert "Conversation test-id deleted." in result.output
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    @patch('main.get_canonical_model')
    @patch('main.get_api_keys')
    @patch('main.initialize_clients')
    @patch('main.display_status')
    def test_main_status(self, mock_display, mock_init_clients, mock_get_keys, 
                        mock_get_model, mock_conv_manager, mock_load_config):
        """Test status display."""
        # Setup mocks
        mock_load_config.return_value = {
            'defaults': {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 1000,
                'template': None
            },
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        
        mock_get_model.return_value = ('gpt-4o', {
            'model': 'gpt-4o',
            'parent': 'openai',
            'apikey': 'OPENAI_API_KEY',
            'api_key_valid': True
        })
        
        mock_get_keys.return_value = {'OPENAI_API_KEY': 'test-key'}
        mock_init_clients.return_value = {'openai': MagicMock()}
        
        runner = CliRunner()
        result = runner.invoke(main.main, ['--status', 'Test query'])
        
        assert result.exit_code == 0
        mock_display.assert_called_once()
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    @patch('main.get_template')
    @patch('main.get_canonical_model')
    @patch('main.get_api_keys')
    @patch('main.initialize_clients')
    @patch('main.query')
    def test_main_with_template(self, mock_query, mock_init_clients, mock_get_keys,
                               mock_get_model, mock_get_template, mock_conv_manager, 
                               mock_load_config):
        """Test query with template."""
        # Setup mocks
        mock_load_config.return_value = {
            'defaults': {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 1000,
                'template': None
            },
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_get_template.return_value = ('test_template', {
            'model': 'claude-3-5-sonnet',
            'temperature': 0.5,
            'systemprompt': 'You are a test assistant.'
        })
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        mock_conv_manager_instance.new_conversation.return_value = MagicMock()
        
        mock_get_model.return_value = ('claude-3-5-sonnet', {
            'model': 'claude-3-5-sonnet',
            'parent': 'anthropic',
            'apikey': 'ANTHROPIC_API_KEY',
            'api_key_valid': True
        })
        
        mock_get_keys.return_value = {'ANTHROPIC_API_KEY': 'test-key'}
        mock_init_clients.return_value = {'anthropic': MagicMock()}
        mock_query.return_value = "Template response"
        
        runner = CliRunner()
        result = runner.invoke(main.main, [
            '--template', 'test_template',
            'Test query'
        ])
        
        assert result.exit_code == 0
        mock_get_template.assert_called_once()
        mock_query.assert_called_once()
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    @patch('main.get_canonical_model')
    @patch('main.get_api_keys')
    @patch('main.initialize_clients')
    @patch('main.get_reference_string')
    @patch('main.query')
    def test_main_with_reference(self, mock_query, mock_get_ref, mock_init_clients,
                                mock_get_keys, mock_get_model, mock_conv_manager, 
                                mock_load_config):
        """Test query with reference files."""
        # Setup mocks
        mock_load_config.return_value = {
            'defaults': {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 1000,
                'template': None
            },
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        mock_conv_manager_instance.new_conversation.return_value = MagicMock()
        
        mock_get_model.return_value = ('gpt-4o', {
            'model': 'gpt-4o',
            'parent': 'openai',
            'apikey': 'OPENAI_API_KEY',
            'api_key_valid': True
        })
        
        mock_get_keys.return_value = {'OPENAI_API_KEY': 'test-key'}
        mock_init_clients.return_value = {'openai': MagicMock()}
        mock_get_ref.return_value = '<reference name="test">Test content</reference>'
        mock_query.return_value = "Reference response"
        
        runner = CliRunner()
        result = runner.invoke(main.main, [
            '--reference', 'test.txt',
            'Test query'
        ])
        
        assert result.exit_code == 0
        mock_get_ref.assert_called_once_with('test.txt')
        mock_query.assert_called_once()
    
    @patch('main.load_config')
    @patch('main.get_canonical_model')
    def test_main_invalid_model(self, mock_get_model, mock_load_config):
        """Test behavior with invalid model."""
        mock_load_config.return_value = {
            'defaults': {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 1000,
                'template': None
            },
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_get_model.return_value = (None, {})
        
        runner = CliRunner()
        result = runner.invoke(main.main, [
            '--model', 'invalid-model',
            'Test query'
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output
    
    def test_main_no_query(self):
        """Test behavior when no query is provided."""
        runner = CliRunner()
        result = runner.invoke(main.main, [])
        
        assert result.exit_code == 1
        assert "Require at least one query" in result.output
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    def test_main_export_conversation(self, mock_conv_manager, mock_load_config):
        """Test exporting a conversation."""
        mock_load_config.return_value = {
            'defaults': {'model': 'gpt-4o'},
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        mock_conv_manager_instance.export_conversation_to_markdown.return_value = "# Conversation\\n\\nContent"
        
        runner = CliRunner()
        result = runner.invoke(main.main, [
            '--export-conversation', 'test-id',
            '--stdout'
        ])
        
        assert result.exit_code == 0
        assert "# Conversation" in result.output
    
    @patch('main.load_config')
    @patch('main.ConversationManager')
    @patch('main.get_canonical_model')
    @patch('main.get_api_keys')
    @patch('main.initialize_clients')
    @patch('main.query')
    def test_main_continue_conversation(self, mock_query, mock_init_clients, 
                                       mock_get_keys, mock_get_model, 
                                       mock_conv_manager, mock_load_config):
        """Test continuing an existing conversation."""
        # Setup mocks
        mock_load_config.return_value = {
            'defaults': {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 1000,
                'template': None
            },
            'paths': {'template_path': 'Agents.json'}
        }
        
        mock_conv_manager_instance = MagicMock()
        mock_conv_manager.return_value = mock_conv_manager_instance
        
        # Mock an existing conversation
        mock_conversation = MagicMock()
        mock_conversation.messages = []
        mock_conversation.get_messages_for_llm.return_value = []
        mock_conv_manager_instance.get_most_recent_conversation.return_value = mock_conversation
        
        mock_get_model.return_value = ('gpt-4o', {
            'model': 'gpt-4o',
            'parent': 'openai',
            'apikey': 'OPENAI_API_KEY',
            'api_key_valid': True
        })
        
        mock_get_keys.return_value = {'OPENAI_API_KEY': 'test-key'}
        mock_init_clients.return_value = {'openai': MagicMock()}
        mock_query.return_value = "Continued response"
        
        runner = CliRunner()
        result = runner.invoke(main.main, [
            '--continue',
            'Continue query'
        ])
        
        assert result.exit_code == 0
        mock_conv_manager_instance.get_most_recent_conversation.assert_called_once()
        mock_query.assert_called_once()

#fin