"""Minimal fake `pipecat` package for keyless, dependency-free unit tests.

The real pipecat-ai package (and its vendor extras) is NOT required to run
the unit test suite. These fakes mirror the exact import paths the agent
uses; an integration run against real pipecat happens on a machine where
it is installed (see tests/test_pipeline.py::test_real_pipecat_imports).
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from typing import Any


class FakeSettings:
    """Stands in for Service.Settings — records whatever it's given."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class _FakeService:
    Settings = FakeSettings

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class FakeDeepgramSTTService(_FakeService):
    pass


class FakeAnthropicLLMService(_FakeService):
    pass


class FakeElevenLabsTTSService(_FakeService):
    pass


class FakePipeline:
    def __init__(self, processors: list[Any]) -> None:
        self.processors = processors


class FakePipelineParams:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class FakePipelineWorker:
    def __init__(self, pipeline: Any, **kwargs: Any) -> None:
        self.pipeline = pipeline
        self.kwargs = kwargs
        self.queued: list[Any] = []

    async def queue_frames(self, frames: list[Any]) -> None:
        self.queued.extend(frames)

    async def cancel(self) -> None:
        self.cancelled = True


class FakePipelineRunner:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.ran: list[Any] = []

    async def run(self, worker: Any) -> None:
        self.ran.append(worker)


class FakeLLMContext:
    def __init__(self, messages: list[dict] | None = None, **kwargs: Any) -> None:
        self.messages = messages or []


class _AggregatorEnd:
    def __init__(self, kind: str) -> None:
        self.kind = kind


class FakeLLMContextAggregatorPair:
    def __init__(self, context: Any, **kwargs: Any) -> None:
        self.context = context
        self._user = _AggregatorEnd("user")
        self._assistant = _AggregatorEnd("assistant")

    def user(self) -> _AggregatorEnd:
        return self._user

    def assistant(self) -> _AggregatorEnd:
        return self._assistant


class FakeFrameDirection:
    DOWNSTREAM = "downstream"
    UPSTREAM = "upstream"


class FakeFrameProcessor:
    def __init__(self, **kwargs: Any) -> None:
        self.pushed: list[Any] = []

    async def process_frame(self, frame: Any, direction: Any) -> None:
        return None

    async def push_frame(self, frame: Any, direction: Any = None) -> None:
        self.pushed.append(frame)


@dataclass
class FakeFrame:
    pass


@dataclass
class FakeTranscriptionFrame(FakeFrame):
    text: str = ""
    user_id: str = ""
    timestamp: str = ""


@dataclass
class FakeTTSTextFrame(FakeFrame):
    text: str = ""


@dataclass
class FakeTTSSpeakFrame(FakeFrame):
    text: str = ""


class FakeTransportParams:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class FakeSileroVADAnalyzer:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


@dataclass
class FakeTransport:
    """Test double for a pipecat transport."""

    handlers: dict[str, Any] = field(default_factory=dict)

    def input(self) -> str:
        return "TRANSPORT_INPUT"

    def output(self) -> str:
        return "TRANSPORT_OUTPUT"

    def event_handler(self, name: str):
        def wrapper(fn):
            self.handlers[name] = fn
            return fn

        return wrapper


def _module(name: str, **attrs: Any) -> types.ModuleType:
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


def install_fake_pipecat() -> dict[str, types.ModuleType | None]:
    """Force fake pipecat modules into sys.modules.

    Returns the previous value for every touched key (None if absent) so the
    caller can restore sys.modules afterwards.
    """
    modules = {
        "pipecat": _module("pipecat"),
        "pipecat.pipeline": _module("pipecat.pipeline"),
        "pipecat.pipeline.pipeline": _module("pipecat.pipeline.pipeline", Pipeline=FakePipeline),
        "pipecat.pipeline.task": _module(
            "pipecat.pipeline.task",
            PipelineWorker=FakePipelineWorker,
            PipelineTask=FakePipelineWorker,
            PipelineParams=FakePipelineParams,
        ),
        "pipecat.pipeline.runner": _module(
            "pipecat.pipeline.runner", PipelineRunner=FakePipelineRunner
        ),
        "pipecat.processors": _module("pipecat.processors"),
        "pipecat.processors.aggregators": _module("pipecat.processors.aggregators"),
        "pipecat.processors.aggregators.llm_context": _module(
            "pipecat.processors.aggregators.llm_context", LLMContext=FakeLLMContext
        ),
        "pipecat.processors.aggregators.llm_response_universal": _module(
            "pipecat.processors.aggregators.llm_response_universal",
            LLMContextAggregatorPair=FakeLLMContextAggregatorPair,
        ),
        "pipecat.processors.frame_processor": _module(
            "pipecat.processors.frame_processor",
            FrameProcessor=FakeFrameProcessor,
            FrameDirection=FakeFrameDirection,
        ),
        "pipecat.frames": _module("pipecat.frames"),
        "pipecat.frames.frames": _module(
            "pipecat.frames.frames",
            Frame=FakeFrame,
            TranscriptionFrame=FakeTranscriptionFrame,
            TTSTextFrame=FakeTTSTextFrame,
            TTSSpeakFrame=FakeTTSSpeakFrame,
        ),
        "pipecat.services": _module("pipecat.services"),
        "pipecat.services.deepgram": _module("pipecat.services.deepgram"),
        "pipecat.services.deepgram.stt": _module(
            "pipecat.services.deepgram.stt", DeepgramSTTService=FakeDeepgramSTTService
        ),
        "pipecat.services.anthropic": _module("pipecat.services.anthropic"),
        "pipecat.services.anthropic.llm": _module(
            "pipecat.services.anthropic.llm", AnthropicLLMService=FakeAnthropicLLMService
        ),
        "pipecat.services.elevenlabs": _module("pipecat.services.elevenlabs"),
        "pipecat.services.elevenlabs.tts": _module(
            "pipecat.services.elevenlabs.tts", ElevenLabsTTSService=FakeElevenLabsTTSService
        ),
        "pipecat.transports": _module("pipecat.transports"),
        "pipecat.transports.base_transport": _module(
            "pipecat.transports.base_transport", TransportParams=FakeTransportParams
        ),
        "pipecat.audio": _module("pipecat.audio"),
        "pipecat.audio.vad": _module("pipecat.audio.vad"),
        "pipecat.audio.vad.silero": _module(
            "pipecat.audio.vad.silero", SileroVADAnalyzer=FakeSileroVADAnalyzer
        ),
    }
    previous: dict[str, types.ModuleType | None] = {}
    for name, mod in modules.items():
        previous[name] = sys.modules.get(name)
        sys.modules[name] = mod
    return previous


def restore_modules(previous: dict[str, types.ModuleType | None]) -> None:
    """Undo install_fake_pipecat()."""
    for name, mod in previous.items():
        if mod is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = mod
