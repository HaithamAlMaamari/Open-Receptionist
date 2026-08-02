"""Anthropic (Claude) LLM provider.

API verified against the Pipecat reference docs (AnthropicLLMService accepts
``settings=AnthropicLLMService.Settings(...)``; the bare ``model`` parameter
is deprecated).
"""

from __future__ import annotations

from typing import Any

from agent.providers.base import LLMProvider, env_int, env_or, require_env

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 1024


class AnthropicLLM(LLMProvider):
    """Claude behind the swappable provider interface.

    Claude is the default LLM for its strong Arabic and tool-use performance,
    but any LLMProvider can replace it via ``LLM_PROVIDER``.
    """

    name = "anthropic"

    def create_service(self, *, model: str | None = None) -> Any:
        from pipecat.services.anthropic.llm import AnthropicLLMService

        api_key = require_env("ANTHROPIC_API_KEY", "Anthropic LLM")
        return AnthropicLLMService(
            api_key=api_key,
            settings=AnthropicLLMService.Settings(
                model=model or env_or("LLM_MODEL", DEFAULT_MODEL),
                max_tokens=env_int("LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS),
            ),
        )
