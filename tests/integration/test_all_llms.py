"""
Integration tests for all enabled LLM providers in dejavu2-cli.

Tests that all enabled LLM families (OpenAI, Anthropic, Google/Gemini, Ollama)
can be properly initialized and routed through the main query system.
"""

import os

# Import functions from the application
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from llm_clients import initialize_clients, query
from models import list_available_canonical_models_with_details


class TestEnabledLLMsIntegration:
  """Integration tests for all enabled LLM providers."""

  @classmethod
  def setup_class(cls):
    """Load enabled models from Models.json."""
    cls.models_config = list_available_canonical_models_with_details("Models/Models.json")
    cls.enabled_models = {k: v for k, v in cls.models_config.items() if v.get("enabled", 0) == 1}

    # Group by provider (parent field) - lowercase for consistency
    cls.providers = {}
    for model, config in cls.enabled_models.items():
      parent = config.get("parent")
      provider = (parent or "unknown").lower()
      if provider not in cls.providers:
        cls.providers[provider] = []
      cls.providers[provider].append(model)

    # Also keep family grouping for series-specific tests
    cls.families = {}
    for model, config in cls.enabled_models.items():
      family = config.get("family", "unknown")
      if family not in cls.families:
        cls.families[family] = []
      cls.families[family].append(model)

  def test_all_enabled_providers_present(self):
    """Test that core LLM providers are enabled."""
    # Core providers that should be present
    core_providers = ["openai", "anthropic", "google"]

    for provider in core_providers:
      assert provider in self.providers, f"Expected core LLM provider '{provider}' not found in enabled models"
      assert len(self.providers[provider]) > 0, f"No models enabled for core provider '{provider}'"

    # Ollama is optional - only check if present
    optional_providers = ["ollama"]
    present_optional = [p for p in optional_providers if p in self.providers and len(self.providers[p]) > 0]

    print(f"✅ Found enabled models for core providers: {core_providers}")
    if present_optional:
      print(f"✅ Optional providers also present: {present_optional}")

  def test_openai_provider_models(self):
    """Test that OpenAI provider models are properly configured."""
    openai_models = self.providers.get("openai", [])
    assert len(openai_models) > 0, "No OpenAI models enabled"

    # Test specific model types
    gpt4_models = [m for m in openai_models if "gpt-4" in m.lower()]
    chatgpt_models = [m for m in openai_models if "chatgpt" in m.lower()]
    o_series = [m for m in openai_models if any(m.startswith(f"o{i}") for i in [1, 3, 4])]

    assert len(gpt4_models) > 0, "No GPT-4 models enabled"
    print(f"✅ OpenAI family: {len(openai_models)} models ({len(gpt4_models)} GPT-4, {len(chatgpt_models)} ChatGPT, {len(o_series)} O-series)")

  def test_anthropic_provider_models(self):
    """Test that Anthropic provider models are properly configured."""
    anthropic_models = self.providers.get("anthropic", [])
    assert len(anthropic_models) > 0, "No Anthropic models enabled"

    # Test specific model types
    claude4_models = [m for m in anthropic_models if "claude-4" in m or "claude-sonnet-4" in m or "claude-haiku-4" in m or "claude-opus-4" in m]
    haiku_models = [m for m in anthropic_models if "haiku" in m]
    sonnet_models = [m for m in anthropic_models if "sonnet" in m]
    opus_models = [m for m in anthropic_models if "opus" in m]

    assert len(claude4_models) > 0, "No Claude 4.x models enabled"
    print(
      f"✅ Anthropic provider: {len(anthropic_models)} models ({len(claude4_models)} Claude 4.x, {len(haiku_models)} Haiku, {len(sonnet_models)} Sonnet, {len(opus_models)} Opus)"
    )

  def test_google_provider_models(self):
    """Test that Google/Gemini provider models are properly configured."""
    google_models = self.providers.get("google", [])
    assert len(google_models) > 0, "No Google/Gemini models enabled"

    # Test specific model types
    gemini20_models = [m for m in google_models if "gemini-2.0" in m]
    gemini25_models = [m for m in google_models if "gemini-2.5" in m]
    flash_models = [m for m in google_models if "flash" in m]
    pro_models = [m for m in google_models if "pro" in m]

    assert len(gemini20_models) > 0 or len(gemini25_models) > 0, "No Gemini 2.0+ models enabled"
    print(
      f"✅ Google provider: {len(google_models)} models ({len(gemini20_models)} 2.0, {len(gemini25_models)} 2.5, {len(flash_models)} Flash, {len(pro_models)} Pro)"
    )

  def test_ollama_provider_models(self):
    """Test that Ollama provider models are properly configured (if enabled)."""
    ollama_models = self.providers.get("ollama", [])

    if len(ollama_models) == 0:
      pytest.skip("No Ollama models enabled in configuration")

    # Test specific model types
    gemma_models = [m for m in ollama_models if "gemma" in m.lower()]
    llama_models = [m for m in ollama_models if "llama" in m.lower()]

    assert len(gemma_models) > 0 or len(llama_models) > 0, "No Gemma or Llama models enabled"
    print(f"✅ Ollama provider: {len(ollama_models)} models ({len(gemma_models)} Gemma, {len(llama_models)} Llama)")


class TestLLMRouting:
  """Test that all enabled LLMs can be properly routed through the main query function."""

  def setup_method(self):
    """Setup for each test method."""
    self.models_config = list_available_canonical_models_with_details("Models/Models.json")
    self.enabled_models = {k: v for k, v in self.models_config.items() if v.get("enabled", 0) == 1}

  def test_openai_routing_with_responses_api(self):
    """Test routing to OpenAI models with Responses API enabled."""
    openai_models = [k for k, v in self.enabled_models.items() if v.get("family") == "openai"]
    if not openai_models:
      pytest.skip("No OpenAI models enabled")

    test_model = openai_models[0]  # Test with first enabled OpenAI model
    model_params = self.models_config[test_model]

    # Mock all dependencies
    with patch("llm_clients.get_openai_client") as mock_get_client, patch("llm_clients.query_openai") as mock_query_openai:
      with patch("llm_clients.validate_query_parameters") as mock_validate:
        with patch("llm_clients.prepare_query_context") as mock_prepare:
          # Setup mocks
          mock_client = MagicMock()
          mock_get_client.return_value = mock_client
          mock_query_openai.return_value = "OpenAI response"
          mock_validate.return_value = 1000
          mock_prepare.return_value = ("test query", "test system", [])

          # Test query routing
          result = query(
            clients={"openai": mock_client},
            query_text="Test query",
            systemprompt="Test system",
            messages=[],
            model=test_model,
            temperature=0.7,
            max_tokens=1000,
            model_parameters=model_params,
            api_keys={"OPENAI_API_KEY": "test-key"},
          )

          assert result == "OpenAI response"
          mock_query_openai.assert_called_once()

          # Verify the call was made with correct parameters
          # query_openai is called with positional args: (client, query, system, model, temperature, max_tokens, ...)
          call_args = mock_query_openai.call_args
          # Check if called with keyword args or positional args
          if call_args.kwargs and "model" in call_args.kwargs:
            assert call_args.kwargs["model"] == test_model
          else:
            # Positional: (client, query, system, model, ...)
            assert call_args.args[3] == test_model  # model is 4th arg (index 3)

  def test_anthropic_routing_with_2025_features(self):
    """Test routing to Anthropic models with 2025 features."""
    anthropic_models = [k for k, v in self.enabled_models.items() if v.get("family") == "anthropic"]
    if not anthropic_models:
      pytest.skip("No Anthropic models enabled")

    test_model = anthropic_models[0]
    model_params = self.models_config[test_model]

    with patch("llm_clients.get_anthropic_client") as mock_get_client, patch("llm_clients.query_anthropic") as mock_query_anthropic:
      with patch("llm_clients.validate_query_parameters") as mock_validate:
        with patch("llm_clients.prepare_query_context") as mock_prepare:
          mock_client = MagicMock()
          mock_get_client.return_value = mock_client
          mock_query_anthropic.return_value = "Anthropic response"
          mock_validate.return_value = 1000
          mock_prepare.return_value = ("test query", "test system", [])

          result = query(
            clients={"anthropic": mock_client},
            query_text="Test query",
            systemprompt="Test system",
            messages=[],
            model=test_model,
            temperature=0.7,
            max_tokens=1000,
            model_parameters=model_params,
            api_keys={"ANTHROPIC_API_KEY": "test-key"},
          )

          assert result == "Anthropic response"
          mock_query_anthropic.assert_called_once()

  def test_google_routing_with_2025_features(self):
    """Test routing to Google/Gemini models with 2025 features."""
    google_models = [k for k, v in self.enabled_models.items() if v.get("family") == "google"]
    if not google_models:
      pytest.skip("No Google models enabled")

    test_model = google_models[0]
    model_params = self.models_config[test_model]

    with patch("llm_clients.validate_google_api_key") as mock_validate_key, patch("llm_clients.query_gemini") as mock_query_gemini:
      with patch("llm_clients.validate_query_parameters") as mock_validate:
        with patch("llm_clients.prepare_query_context") as mock_prepare:
          mock_validate_key.return_value = "test-google-key"
          mock_query_gemini.return_value = "Gemini response"
          mock_validate.return_value = 1000
          mock_prepare.return_value = ("test query", "test system", [])

          result = query(
            clients={"google": True},
            query_text="Test query",
            systemprompt="Test system",
            messages=[],
            model=test_model,
            temperature=0.7,
            max_tokens=1000,
            model_parameters=model_params,
            api_keys={"GOOGLE_API_KEY": "test-key"},
          )

          assert result == "Gemini response"
          mock_query_gemini.assert_called_once()

  def test_ollama_routing_local_and_remote(self):
    """Test routing to Ollama models (both local and remote)."""
    ollama_models = [k for k, v in self.enabled_models.items() if v.get("family") == "ollama"]
    if not ollama_models:
      pytest.skip("No Ollama models enabled")

    test_model = ollama_models[0]
    model_params = self.models_config[test_model]

    with patch("llm_clients.get_ollama_client") as mock_get_client, patch("llm_clients.query_llama") as mock_query_llama:
      with patch("llm_clients.validate_query_parameters") as mock_validate:
        with patch("llm_clients.prepare_query_context") as mock_prepare:
          mock_client = MagicMock()
          mock_get_client.return_value = mock_client
          mock_query_llama.return_value = "Llama response"
          mock_validate.return_value = 1000
          mock_prepare.return_value = ("test query", "test system", [])

          result = query(
            clients={"ollama": mock_client, "ollama_local": mock_client},
            query_text="Test query",
            systemprompt="Test system",
            messages=[],
            model=test_model,
            temperature=0.7,
            max_tokens=1000,
            model_parameters=model_params,
            api_keys={"OLLAMA_API_KEY": "test-key"},
          )

          assert result == "Llama response"
          mock_query_llama.assert_called_once()


class TestModelParametersForAllFamilies:
  """Test that all enabled models have proper parameters configured."""

  def setup_method(self):
    """Setup for each test method."""
    self.models_config = list_available_canonical_models_with_details("Models/Models.json")
    self.enabled_models = {k: v for k, v in self.models_config.items() if v.get("enabled", 0) == 1}

  def test_all_enabled_models_have_required_parameters(self):
    """Test that all enabled models have required parameters."""
    required_params = ["family", "model", "max_output_tokens"]

    for model_name, config in self.enabled_models.items():
      for param in required_params:
        assert param in config, f"Model '{model_name}' missing required parameter '{param}'"

      # Test family-specific requirements
      family = config.get("family")
      if family == "openai":
        # OpenAI models should either have OPENAI_API_KEY or None (using default)
        api_key = config.get("apikey")
        assert api_key in [None, "OPENAI_API_KEY"], f"OpenAI model '{model_name}' has unexpected apikey: {api_key}"
      elif family == "anthropic":
        api_key = config.get("apikey")
        assert api_key in [None, "ANTHROPIC_API_KEY"], f"Anthropic model '{model_name}' has unexpected apikey: {api_key}"
      elif family == "google":
        # Google models may use GOOGLE_API_KEY, GEMINI_API_KEY, or None
        api_key = config.get("apikey")
        assert api_key in [None, "GOOGLE_API_KEY", "GEMINI_API_KEY"], f"Google model '{model_name}' has unexpected apikey: {api_key}"
      elif family == "ollama":
        # Ollama models may use different API key setups
        pass

  def test_model_parameters_retrieval(self):
    """Test that model parameters can be retrieved for all enabled models."""
    for model_name in self.enabled_models:
      params = self.models_config[model_name]

      assert params is not None, f"Could not get parameters for model '{model_name}'"
      assert "family" in params, f"Model '{model_name}' parameters missing 'family'"
      assert "max_output_tokens" in params, f"Model '{model_name}' parameters missing 'max_output_tokens'"

  def test_context_window_limits(self):
    """Test that all models have reasonable context window limits."""
    for model_name, config in self.enabled_models.items():
      context_window = config.get("context_window", 0)
      max_output = config.get("max_output_tokens", 0)

      # Skip special models that may not have standard context windows
      if any(skip_word in model_name.lower() for skip_word in ["moderation", "embedding", "tts", "whisper", "dall-e", "image"]):
        continue

      assert context_window > 0, f"Model '{model_name}' has invalid context_window: {context_window}"
      assert max_output > 0, f"Model '{model_name}' has invalid max_output_tokens: {max_output}"
      assert max_output <= context_window, f"Model '{model_name}' max_output_tokens ({max_output}) exceeds context_window ({context_window})"


class TestClientInitialization:
  """Test that clients can be initialized for all enabled LLM families."""

  def test_client_initialization_all_families(self):
    """Test that clients can be initialized for all enabled families."""
    api_keys = {
      "OPENAI_API_KEY": "test-openai-key",
      "ANTHROPIC_API_KEY": "test-anthropic-key",
      "GOOGLE_API_KEY": "test-google-key",
      "OLLAMA_API_KEY": "test-ollama-key",
    }

    with patch("llm_clients.OpenAI") as mock_openai, patch("llm_clients.Anthropic") as mock_anthropic, patch("llm_clients.genai"):
      # Mock client instances
      mock_openai_instance = MagicMock()
      mock_anthropic_instance = MagicMock()
      mock_openai.return_value = mock_openai_instance
      mock_anthropic.return_value = mock_anthropic_instance

      clients = initialize_clients(api_keys)

      # Verify all expected clients are present
      expected_clients = ["openai", "anthropic", "google", "ollama", "ollama_local"]
      for client_name in expected_clients:
        assert client_name in clients, f"Client '{client_name}' not initialized"

      # Verify client types
      assert clients["openai"] == mock_openai_instance
      assert clients["anthropic"] == mock_anthropic_instance
      assert clients["google"] is not None  # Google now uses genai.Client instance
      assert clients["ollama"] is not None
      assert clients["ollama_local"] is not None


class TestEndToEndMockIntegration:
  """End-to-end integration tests with mocked LLM responses."""

  def test_sample_model_from_each_family(self):
    """Test a sample model from each enabled family end-to-end."""
    models_config = list_available_canonical_models_with_details("Models/Models.json")
    enabled_models = {k: v for k, v in models_config.items() if v.get("enabled", 0) == 1}

    # Get one model from each family
    families = {}
    for model, config in enabled_models.items():
      family = config.get("family")
      if family not in families:
        families[family] = model

    expected_families = ["openai", "anthropic", "google", "ollama"]
    for family in expected_families:
      if family not in families:
        pytest.skip(f"No enabled models found for family: {family}")

    # Test each family
    test_cases = [
      ("openai", families["openai"], "OpenAI response"),
      ("anthropic", families["anthropic"], "Anthropic response"),
      ("google", families["google"], "Gemini response"),
      ("ollama", families["ollama"], "Llama response"),
    ]

    for family, model_name, expected_response in test_cases:
      model_params = models_config[model_name]

      # Create appropriate mocks for each family
      if family == "openai":
        with patch("llm_clients.query_openai") as mock_query:
          mock_query.return_value = expected_response
          self._test_query_with_mocks(model_name, model_params, expected_response, {family: MagicMock()})
      elif family == "anthropic":
        with patch("llm_clients.query_anthropic") as mock_query:
          mock_query.return_value = expected_response
          self._test_query_with_mocks(model_name, model_params, expected_response, {family: MagicMock()})
      elif family == "google":
        with patch("llm_clients.query_gemini") as mock_query:
          mock_query.return_value = expected_response
          self._test_query_with_mocks(model_name, model_params, expected_response, {family: True})
      elif family == "ollama":
        with patch("llm_clients.query_llama") as mock_query:
          mock_query.return_value = expected_response
          self._test_query_with_mocks(model_name, model_params, expected_response, {family: MagicMock(), "ollama_local": MagicMock()})

  def _test_query_with_mocks(self, model_name, model_params, expected_response, clients):
    """Helper method to test query with mocked responses."""
    api_keys = {
      "OPENAI_API_KEY": "test-openai",
      "ANTHROPIC_API_KEY": "test-anthropic",
      "GOOGLE_API_KEY": "test-google",
      "OLLAMA_API_KEY": "test-ollama",
    }

    result = query(
      clients=clients,
      query_text="Test query for " + model_name,
      systemprompt="You are a helpful assistant",
      messages=[],
      model=model_name,
      temperature=0.7,
      max_tokens=1000,
      model_parameters=model_params,
      api_keys=api_keys,
    )

    assert result == expected_response, f"Unexpected response for model {model_name}"


if __name__ == "__main__":
  pytest.main([__file__, "-v"])
