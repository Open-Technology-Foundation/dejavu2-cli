"""
Shared test fixtures and configuration for dejavu2-cli tests.
"""
import os
import pytest
import tempfile
import yaml

@pytest.fixture(scope="session")
def temp_config_dir():
    """Create a temporary directory for config files during testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture(scope="session")
def mock_api_keys():
    """Set up mock API keys for testing, and restore original environment after."""
    # Save original environment variables
    original_openai = os.environ.get('OPENAI_API_KEY')
    original_anthropic = os.environ.get('ANTHROPIC_API_KEY')
    
    # Set mock values for testing
    os.environ['OPENAI_API_KEY'] = 'mock-openai-key-for-testing'
    os.environ['ANTHROPIC_API_KEY'] = 'mock-anthropic-key-for-testing'
    
    yield
    
    # Restore original environment
    if original_openai is not None:
        os.environ['OPENAI_API_KEY'] = original_openai
    else:
        del os.environ['OPENAI_API_KEY']
        
    if original_anthropic is not None:
        os.environ['ANTHROPIC_API_KEY'] = original_anthropic
    else:
        del os.environ['ANTHROPIC_API_KEY']