"""Flexible LLM client for the IMTI system.

This client works with ANY OpenAI-compatible API by changing three env vars:
- LLM_API_BASE_URL: The API endpoint (OpenAI, Anthropic via proxy, Groq, Ollama, etc.)
- LLM_API_KEY: The API key for the provider
- LLM_MODEL: The model name to use

Examples of supported configurations:
  OpenAI:       LLM_API_BASE_URL=https://api.openai.com/v1           LLM_MODEL=gpt-4o-mini
  Anthropic:    LLM_API_BASE_URL=https://api.anthropic.com/v1         LLM_MODEL=claude-3-haiku-20240307
  Groq:         LLM_API_BASE_URL=https://api.groq.com/openai/v1      LLM_MODEL=llama-3.1-8b-instant
  Together AI:  LLM_API_BASE_URL=https://api.together.xyz/v1         LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
  Ollama local: LLM_API_BASE_URL=http://localhost:11434/v1           LLM_MODEL=llama3
  Azure OpenAI: LLM_API_BASE_URL=https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT  LLM_MODEL=gpt-4o-mini
  Any custom:   Just set the base URL, API key, and model name

The client uses the OpenAI Python SDK which supports any OpenAI-compatible API
through the `base_url` parameter.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from imti.config.settings import get_settings
from imti.core.logger import get_logger

logger = get_logger("llm")


class LLMResponse(BaseModel):
    """Structured response from the LLM."""

    content: str
    model: str
    usage_prompt_tokens: int = 0
    usage_completion_tokens: int = 0
    finish_reason: str = ""
    raw_response: dict[str, Any] | None = None


class LLMClient:
    """Flexible LLM client that works with any OpenAI-compatible API.

    Configuration is 100% driven by environment variables:
    - LLM_API_KEY: API key (required)
    - LLM_API_BASE_URL: Base URL of the API (default: OpenAI)
    - LLM_MODEL: Model name to use (default: gpt-4o-mini)
    - LLM_MAX_TOKENS: Max completion tokens (default: 1024)

    Swap providers by just changing these env vars — no code changes needed.
    """

    def __init__(self) -> None:
        """Initialize the LLM client from environment settings."""
        settings = get_settings()
        self._api_key = settings.llm_api_key
        self._base_url = settings.llm_api_base_url
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens
        self._configured = settings.llm_is_configured

        if self._configured:
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
            logger.info(
                f"LLM client configured: base_url={self._base_url}, model={self._model}"
            )
        else:
            self._client = None
            logger.warning(
                "LLM client NOT configured — set LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL"
            )

    @property
    def is_configured(self) -> bool:
        """Check if the LLM client is ready to make calls."""
        return self._configured and self._client is not None

    @property
    def model_name(self) -> str:
        """Current model name."""
        return self._model

    @property
    def provider_info(self) -> str:
        """Human-readable provider info for logging/display."""
        return f"model={self._model} @ {self._base_url}"

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request to the LLM.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            temperature: Sampling temperature (0 = deterministic, 1 = creative)
            max_tokens: Override max completion tokens for this call
            response_format: Optional {"type": "json_object"} for JSON mode

        Returns:
            LLMResponse with content, model, and usage info

        Raises:
            RuntimeError: If LLM client is not configured
        """
        if not self.is_configured:
            raise RuntimeError(
                "LLM client not configured. Set LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL env vars."
            )

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]

            choice = response.choices[0]
            content = choice.message.content or ""

            return LLMResponse(
                content=content,
                model=response.model,
                usage_prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                usage_completion_tokens=response.usage.completion_tokens if response.usage else 0,
                finish_reason=choice.finish_reason or "",
            )
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send a chat request expecting JSON response.

        Uses the OpenAI JSON mode and parses the response.

        Returns:
            Parsed JSON dictionary from the LLM response.
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(response.content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}\nContent: {response.content[:500]}")
            raise

    def simple_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> str:
        """Simple single-turn prompt. Returns just the text response.

        Args:
            system_prompt: System instructions
            user_prompt: User message / question
            temperature: Sampling temperature

        Returns:
            The LLM's text response.
        """
        response = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return response.content


# Singleton instance with thread-safe caching
@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance (cached)."""
    return LLMClient()
