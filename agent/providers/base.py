"""Abstract provider interfaces for STT, LLM, and TTS vendors.

A provider is a thin factory that knows how to construct the corresponding
Pipecat service (frame processor) for one vendor. All vendor SDK / Pipecat
service imports happen lazily inside ``create_service`` so that importing
this package never requires vendor extras to be installed.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class ProviderError(RuntimeError):
    """Raised when a provider is misconfigured (e.g. missing API key)."""


def require_env(var: str, provider: str) -> str:
    """Fetch a required environment variable or raise a clear error."""
    value = os.getenv(var, "").strip()
    if not value:
        raise ProviderError(
            f"{provider} requires the {var} environment variable. "
            f"Add it to your .env (see .env.example)."
        )
    return value


def env_or(var: str, default: str) -> str:
    """Optional env variable; empty or whitespace-only counts as unset.

    Prevents ``DEEPGRAM_MODEL=`` (uncommented but unfilled in .env) from
    sending an empty model name to a vendor.
    """
    value = os.getenv(var, "").strip()
    return value or default


def env_int(var: str, default: int) -> int:
    """Optional integer env variable with a clear error naming the variable."""
    raw = os.getenv(var, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ProviderError(f"{var} must be an integer, got {raw!r}") from exc


class STTProvider(ABC):
    """Speech-to-text provider interface."""

    name: str

    @abstractmethod
    def create_service(self, *, language: str = "multi") -> Any:
        """Build the Pipecat STT service. ``language`` is a BCP-47-ish code
        or ``"multi"`` for multilingual transcription (the bilingual default)."""


class LLMProvider(ABC):
    """Large language model provider interface."""

    name: str

    @abstractmethod
    def create_service(self, *, model: str | None = None) -> Any:
        """Build the Pipecat LLM service."""


class TTSProvider(ABC):
    """Text-to-speech provider interface."""

    name: str

    @abstractmethod
    def create_service(self, *, voice: str | None = None) -> Any:
        """Build the Pipecat TTS service. ``voice`` must support Arabic and
        English output for the bilingual default experience."""
