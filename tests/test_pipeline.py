"""The pipeline must construct keylessly, in order, with full transcript coverage."""

from __future__ import annotations

import asyncio
import json
import os

import pytest

from agent.pipeline import build_pipeline
from tests.fakes import FakeTransport


def test_pipeline_constructs(fake_pipecat, business_config) -> None:
    built = build_pipeline(FakeTransport(), business_config)
    assert built.pipeline is not None
    assert built.context is not None
    assert built.aggregator_pair is not None
    assert built.transcript is not None


def test_pipeline_processor_order(fake_pipecat, business_config) -> None:
    """in → STT → caller log → user agg → LLM → TTS → agent log → out → assistant agg."""
    built = build_pipeline(FakeTransport(), business_config)
    procs = built.pipeline.processors

    assert procs[0] == "TRANSPORT_INPUT"
    assert type(procs[1]).__name__.endswith("DeepgramSTTService")
    assert type(procs[2]).__name__ == "TranscriptLogger" and procs[2].side == "caller"
    assert procs[3].kind == "user"
    assert type(procs[4]).__name__.endswith("AnthropicLLMService")
    assert type(procs[5]).__name__.endswith("ElevenLabsTTSService")
    assert type(procs[6]).__name__ == "TranscriptLogger" and procs[6].side == "agent"
    assert procs[7] == "TRANSPORT_OUTPUT"
    assert procs[8].kind == "assistant"
    assert len(procs) == 9
    # Both loggers must share one store → one transcript file per session.
    assert procs[2].store is procs[6].store is built.transcript


def test_system_prompt_seeded_into_context_bilingually(fake_pipecat, business_config) -> None:
    built = build_pipeline(FakeTransport(), business_config)
    messages = built.context.messages
    assert messages[0]["role"] == "system"
    content = messages[0]["content"]
    # Grounded in config — and facts must be present in BOTH languages so an
    # English caller is not answered from machine-translated Arabic facts.
    assert business_config.name_ar in content
    assert business_config.human_phone in content
    assert business_config.services[0].name_ar in content
    assert business_config.services[0].name_en in content
    assert business_config.faq[0].answer_ar in content
    assert business_config.faq[0].answer_en in content


def test_assembled_pipeline_logs_both_sides(
    fake_pipecat, business_config, tmp_path, monkeypatch
) -> None:
    """Compliance default #3, tested through the ASSEMBLED pipeline's loggers.

    Drives frames through the actual TranscriptLogger instances wired into
    the pipeline (not an isolated processor) and asserts caller and agent
    both land in one session JSONL file.
    """
    monkeypatch.setenv("TRANSCRIPT_DIR", str(tmp_path))
    from pipecat.frames.frames import TranscriptionFrame, TTSTextFrame

    built = build_pipeline(FakeTransport(), business_config)
    procs = built.pipeline.processors
    caller_logger, agent_logger = procs[2], procs[6]

    async def scenario() -> None:
        # Caller speaks (frame emitted by STT reaches the caller logger)...
        await caller_logger.process_frame(TranscriptionFrame(text="أبغى موعد بكرة"), "down")
        # ...agent replies (frame emitted by TTS reaches the agent logger),
        # and the agent logger must NOT double-log caller frames.
        await agent_logger.process_frame(TranscriptionFrame(text="should-not-log"), "down")
        await agent_logger.process_frame(TTSTextFrame(text="Of course, what time?"), "down")

    asyncio.run(scenario())

    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1, "both loggers must write to one shared session file"
    entries = [json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines()]
    assert [(e["role"], e["text"]) for e in entries] == [
        ("caller", "أبغى موعد بكرة"),
        ("agent", "Of course, what time?"),
    ]


def test_run_bot_greets_with_ai_disclosure_on_connect(fake_pipecat, monkeypatch, tmp_path) -> None:
    """The compliance-critical path: connecting a client queues verbatim
    greetings that disclose the AI in every configured language."""
    from tests.conftest import EXAMPLE_CONFIG

    monkeypatch.setenv("BUSINESS_CONFIG", str(EXAMPLE_CONFIG))
    monkeypatch.setenv("TRANSCRIPT_DIR", str(tmp_path))

    from agent.bot import run_bot

    transport = FakeTransport()
    worker = asyncio.run(run_bot(transport))

    assert "on_client_connected" in transport.handlers
    assert "on_client_disconnected" in transport.handlers

    asyncio.run(transport.handlers["on_client_connected"](transport, object()))

    texts = [frame.text for frame in worker.queued]
    assert len(texts) == 2, "one greeting frame per configured language"
    assert "مساعد ذكاء اصطناعي" in texts[0], "Arabic (default) greeting speaks first"
    assert "AI assistant" in texts[1]

    asyncio.run(transport.handlers["on_client_disconnected"](transport, object()))
    assert getattr(worker, "cancelled", False) is True


@pytest.mark.skipif(
    os.getenv("RUN_PIPECAT_INTEGRATION") != "1",
    reason="set RUN_PIPECAT_INTEGRATION=1 on a machine with pipecat-ai installed",
)
def test_real_pipecat_imports() -> None:
    """Integration smoke test: the import paths and constructor surface we
    rely on exist in real pipecat."""
    from pipecat.frames.frames import TranscriptionFrame, TTSSpeakFrame, TTSTextFrame  # noqa: F401
    from pipecat.pipeline.pipeline import Pipeline  # noqa: F401
    from pipecat.pipeline.runner import PipelineRunner  # noqa: F401
    from pipecat.pipeline.task import PipelineParams, PipelineWorker  # noqa: F401
    from pipecat.processors.aggregators.llm_context import LLMContext  # noqa: F401
    from pipecat.processors.aggregators.llm_response_universal import (  # noqa: F401
        LLMContextAggregatorPair,
    )
    from pipecat.runner.types import RunnerArguments  # noqa: F401
    from pipecat.runner.utils import create_transport  # noqa: F401
    from pipecat.services.anthropic.llm import AnthropicLLMService
    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
    from pipecat.transports.base_transport import TransportParams  # noqa: F401

    # The Settings alias this codebase configures services through.
    for service in (DeepgramSTTService, AnthropicLLMService, ElevenLabsTTSService):
        assert hasattr(service, "Settings"), f"{service.__name__}.Settings missing"
