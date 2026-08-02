"""Provider registry: env/config-driven selection of STT/LLM/TTS vendors.

Selection order: explicit argument > environment variable > project default.
Community providers register themselves via the ``register_*`` functions.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TypeVar

from agent.providers.anthropic import AnthropicLLM
from agent.providers.base import LLMProvider, ProviderError, STTProvider, TTSProvider
from agent.providers.deepgram import DeepgramSTT
from agent.providers.elevenlabs import ElevenLabsTTS

_STT: dict[str, Callable[[], STTProvider]] = {"deepgram": DeepgramSTT}
_LLM: dict[str, Callable[[], LLMProvider]] = {"anthropic": AnthropicLLM}
_TTS: dict[str, Callable[[], TTSProvider]] = {"elevenlabs": ElevenLabsTTS}

DEFAULTS = {"stt": "deepgram", "llm": "anthropic", "tts": "elevenlabs"}


def register_stt_provider(name: str, factory: Callable[[], STTProvider]) -> None:
    _STT[name.lower()] = factory


def register_llm_provider(name: str, factory: Callable[[], LLMProvider]) -> None:
    _LLM[name.lower()] = factory


def register_tts_provider(name: str, factory: Callable[[], TTSProvider]) -> None:
    _TTS[name.lower()] = factory


_P = TypeVar("_P", STTProvider, LLMProvider, TTSProvider)


def _resolve(
    kind: str, registry: dict[str, Callable[[], _P]], name: str | None, env_var: str
) -> _P:
    chosen = (name or os.getenv(env_var) or DEFAULTS[kind]).strip().lower()
    if chosen not in registry:
        raise ProviderError(
            f"Unknown {kind.upper()} provider {chosen!r} (from {env_var}). "
            f"Available: {', '.join(sorted(registry))}"
        )
    return registry[chosen]()


def get_stt_provider(name: str | None = None) -> STTProvider:
    return _resolve("stt", _STT, name, "STT_PROVIDER")


def get_llm_provider(name: str | None = None) -> LLMProvider:
    return _resolve("llm", _LLM, name, "LLM_PROVIDER")


def get_tts_provider(name: str | None = None) -> TTSProvider:
    return _resolve("tts", _TTS, name, "TTS_PROVIDER")
