"""Provider abstraction layer.

Every AI vendor (STT/LLM/TTS) sits behind an interface here — pipeline logic
never calls a vendor SDK directly, so providers are swappable via env/config
(``STT_PROVIDER``, ``LLM_PROVIDER``, ``TTS_PROVIDER``).
"""

from agent.providers.base import LLMProvider, STTProvider, TTSProvider
from agent.providers.registry import (
    get_llm_provider,
    get_stt_provider,
    get_tts_provider,
    register_llm_provider,
    register_stt_provider,
    register_tts_provider,
)

__all__ = [
    "LLMProvider",
    "STTProvider",
    "TTSProvider",
    "get_llm_provider",
    "get_stt_provider",
    "get_tts_provider",
    "register_llm_provider",
    "register_stt_provider",
    "register_tts_provider",
]
