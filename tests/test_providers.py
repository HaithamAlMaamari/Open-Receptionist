"""Provider registry: env-driven selection, clear errors, lazy vendor imports."""

from __future__ import annotations

import pytest

from agent.providers import get_llm_provider, get_stt_provider, get_tts_provider
from agent.providers.base import ProviderError


def test_defaults(monkeypatch) -> None:
    for var in ("STT_PROVIDER", "LLM_PROVIDER", "TTS_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    assert get_stt_provider().name == "deepgram"
    assert get_llm_provider().name == "anthropic"
    assert get_tts_provider().name == "elevenlabs"


def test_env_selection_is_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "DeepGram")
    assert get_stt_provider().name == "deepgram"


def test_unknown_provider_raises_with_available_list(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gpt-9000")
    with pytest.raises(ProviderError, match="anthropic"):
        get_llm_provider()


def test_missing_api_key_raises_clear_error(fake_pipecat, monkeypatch) -> None:
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="DEEPGRAM_API_KEY"):
        get_stt_provider().create_service()


def test_services_construct_with_fake_pipecat(fake_pipecat) -> None:
    stt = get_stt_provider().create_service(language="multi")
    llm = get_llm_provider().create_service()
    tts = get_tts_provider().create_service()
    assert type(stt).__name__.endswith("DeepgramSTTService")
    assert type(llm).__name__.endswith("AnthropicLLMService")
    assert type(tts).__name__.endswith("ElevenLabsTTSService")
    # Bilingual defaults: multilingual STT + multilingual TTS model.
    assert stt.kwargs["settings"].kwargs["language"] == "multi"
    assert tts.kwargs["settings"].kwargs["model"] == "eleven_multilingual_v2"


def test_importing_providers_needs_no_vendor_sdks() -> None:
    """The provider package must import cleanly without pipecat installed."""
    import agent.providers  # noqa: F401
