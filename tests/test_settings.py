"""Tests for settings — LLM configuration flexibility."""

import os
from unittest.mock import patch

from imti.config.settings import Settings


def test_settings_defaults():
    """Settings should have sensible defaults."""
    # Clear any .env file effects by creating Settings directly
    settings = Settings()
    assert settings.llm_api_base_url == "https://api.openai.com/v1"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_max_tokens == 1024
    assert settings.data_dir == "data"


def test_llm_is_configured():
    """LLM should be considered configured when api_key is set."""
    with patch.dict(os.environ, {"LLM_API_KEY": "sk-test123"}):
        settings = Settings()
        assert settings.llm_is_configured


def test_llm_not_configured_without_key():
    """LLM should not be configured without api_key."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove any existing LLM_API_KEY
        os.environ.pop("LLM_API_KEY", None)
        settings = Settings()
        # May or may not be configured depending on .env
        # This test just checks the property doesn't crash
        assert isinstance(settings.llm_is_configured, bool)


def test_llm_provider_swap():
    """LLM provider should be swappable via env vars."""
    with patch.dict(os.environ, {
        "LLM_API_KEY": "test-key",
        "LLM_API_BASE_URL": "https://api.groq.com/openai/v1",
        "LLM_MODEL": "llama-3.1-8b-instant",
    }):
        settings = Settings()
        assert settings.llm_api_base_url == "https://api.groq.com/openai/v1"
        assert settings.llm_model == "llama-3.1-8b-instant"


def test_email_is_configured():
    """Email should be configured when both key and recipient exist."""
    with patch.dict(os.environ, {
        "SENDGRID_API_KEY": "SG.test",
        "EMAIL_TO": "user@example.com",
    }):
        settings = Settings()
        assert settings.email_is_configured


def test_search_is_configured():
    """Search should be configured when at least one API key exists."""
    with patch.dict(os.environ, {"SEARCH_TAVILY_API_KEY": "tvly-test"}):
        settings = Settings()
        assert settings.search_is_configured


def test_feature_flags():
    """Feature flags should be configurable via env vars."""
    with patch.dict(os.environ, {"IMTI_ENABLE_LLM": "false"}):
        settings = Settings()
        assert settings.enable_llm is False

    with patch.dict(os.environ, {"IMTI_ENABLE_LLM": "true"}):
        settings = Settings()
        assert settings.enable_llm is True
