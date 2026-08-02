"""Pipecat pipeline assembly: Transport in → STT → LLM → TTS → Transport out.

All vendor services are created through the provider registry — this module
contains no vendor-specific code. Pipecat imports are local to the builder so
the module can be imported (and unit-tested) without pipecat installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.config import BusinessConfig
from agent.prompt_loader import render_system_prompt
from agent.providers import get_llm_provider, get_stt_provider, get_tts_provider


@dataclass
class BuiltPipeline:
    """The assembled pipeline plus the pieces the bot runner needs."""

    pipeline: Any
    context: Any
    aggregator_pair: Any
    transcript: Any


def build_pipeline(transport: Any, config: BusinessConfig) -> BuiltPipeline:
    """Assemble the voice pipeline for one session.

    Order: transport.input() → STT → caller transcript logger → user context
    aggregator → LLM → TTS → agent transcript logger → transport.output() →
    assistant context aggregator. Both transcript loggers share one store, so
    each session yields a single JSONL file covering both sides (compliance
    default #3).
    """
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair,
    )

    from agent.transcript import TranscriptLogger, TranscriptStore

    stt = get_stt_provider().create_service(language="multi")
    llm = get_llm_provider().create_service()
    tts = get_tts_provider().create_service()

    system_prompt = render_system_prompt(config)
    context = LLMContext(messages=[{"role": "system", "content": system_prompt}])
    aggregators = LLMContextAggregatorPair(context)

    store = TranscriptStore()

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            TranscriptLogger(store, side="caller"),
            aggregators.user(),
            llm,
            tts,
            TranscriptLogger(store, side="agent"),
            transport.output(),
            aggregators.assistant(),
        ]
    )
    return BuiltPipeline(
        pipeline=pipeline,
        context=context,
        aggregator_pair=aggregators,
        transcript=store,
    )
