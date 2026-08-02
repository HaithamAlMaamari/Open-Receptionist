"""ElevenLabs text-to-speech provider.

API verified against the Pipecat reference docs (ElevenLabsTTSService accepts
``settings=ElevenLabsTTSService.Settings(voice=..., model=...)``; the bare
``voice_id``/``model`` parameters are deprecated).
"""

from __future__ import annotations

from typing import Any

from agent.providers.base import TTSProvider, env_or, require_env

# Multilingual model is required for Arabic output — the default flash model
# is English-focused.
DEFAULT_MODEL = "eleven_multilingual_v2"


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs TTS behind the swappable provider interface."""

    name = "elevenlabs"

    def create_service(self, *, voice: str | None = None) -> Any:
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

        api_key = require_env("ELEVENLABS_API_KEY", "ElevenLabs TTS")
        voice = voice or require_env("ELEVENLABS_VOICE_ID", "ElevenLabs TTS")
        return ElevenLabsTTSService(
            api_key=api_key,
            settings=ElevenLabsTTSService.Settings(
                voice=voice,
                model=env_or("ELEVENLABS_MODEL", DEFAULT_MODEL),
            ),
        )
