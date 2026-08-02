"""Deepgram speech-to-text provider.

API verified against the Pipecat reference docs (DeepgramSTTService accepts
``settings=DeepgramSTTService.Settings(...)``; the legacy ``live_options``
parameter is deprecated). Nova-3 supports Arabic across dialects.
"""

from __future__ import annotations

from typing import Any

from agent.providers.base import STTProvider, env_or, require_env

DEFAULT_MODEL = "nova-3-general"


class DeepgramSTT(STTProvider):
    """Deepgram STT behind the swappable provider interface.

    ``language="multi"`` enables multilingual transcription — the right
    default for Arabic/English code-switching callers. Verify Arabic quality
    at first light; ``DEEPGRAM_LANGUAGE=ar`` forces single-language Arabic if
    code-switching mode underperforms for your dialect.
    """

    name = "deepgram"

    def create_service(self, *, language: str = "multi") -> Any:
        from pipecat.services.deepgram.stt import DeepgramSTTService

        api_key = require_env("DEEPGRAM_API_KEY", "Deepgram STT")
        return DeepgramSTTService(
            api_key=api_key,
            settings=DeepgramSTTService.Settings(
                model=env_or("DEEPGRAM_MODEL", DEFAULT_MODEL),
                language=env_or("DEEPGRAM_LANGUAGE", language),
                punctuate=True,
                smart_format=True,
            ),
        )
