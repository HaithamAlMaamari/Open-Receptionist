"""Shared fixtures: repo paths, example config, and the fake pipecat runtime."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.config import BusinessConfig, load_business_config  # noqa: E402
from tests.fakes import install_fake_pipecat, restore_modules  # noqa: E402

EXAMPLE_CONFIG = REPO_ROOT / "config" / "business.example.yaml"

# Modules that bind pipecat symbols at import time; they must be re-imported
# inside the fake-pipecat window.
_AGENT_MODULES_USING_PIPECAT = ["agent.transcript"]


@pytest.fixture
def business_config() -> BusinessConfig:
    """The shipped dental-clinic example config, fully validated."""
    return load_business_config(EXAMPLE_CONFIG)


@pytest.fixture
def fake_pipecat(monkeypatch: pytest.MonkeyPatch):
    """Run a test against the fake pipecat package, with dummy provider keys.

    Forces fakes even if real pipecat is installed, so unit tests stay
    deterministic and keyless everywhere; sys.modules is restored afterwards.
    """
    saved_agent_modules = {
        name: sys.modules.pop(name, None) for name in _AGENT_MODULES_USING_PIPECAT
    }
    previous = install_fake_pipecat()

    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "test-voice")
    monkeypatch.delenv("TRANSCRIPT_DIR", raising=False)

    yield

    restore_modules(previous)
    for name in _AGENT_MODULES_USING_PIPECAT:
        sys.modules.pop(name, None)
        if saved_agent_modules[name] is not None:
            sys.modules[name] = saved_agent_modules[name]
