"""Call/chat transcript logging (compliance default — always on).

Both sides of the conversation are recorded: a caller-side logger placed
after STT captures ``TranscriptionFrame``s, and an agent-side logger placed
after TTS captures ``TTSTextFrame``s (everything the agent actually speaks,
including the AI-disclosure greeting). Both share one ``TranscriptStore`` so
a session produces a single JSONL file under ``TRANSCRIPT_DIR``.

Milestone 2 moves storage into Postgres. Never commit real transcripts or
audio to the repo. Caller/agent text is written to the transcript file, not
to stdout — set ``TRANSCRIPT_ECHO=1`` to additionally echo it to the logger
during local debugging.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pipecat.frames.frames import Frame, TranscriptionFrame, TTSTextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

logger = logging.getLogger("open_receptionist.transcript")


class TranscriptStore:
    """One transcript sink per session, shared by both pipeline loggers."""

    def __init__(self, session_id: str | None = None) -> None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.session_id = session_id or f"{stamp}-{uuid.uuid4().hex[:8]}"
        self._echo = os.getenv("TRANSCRIPT_ECHO", "").strip() == "1"
        self._path: Path | None = None
        transcript_dir = os.getenv("TRANSCRIPT_DIR", "").strip()
        if transcript_dir:
            directory = Path(transcript_dir)
            directory.mkdir(parents=True, exist_ok=True)
            self._path = directory / f"{self.session_id}.jsonl"

    @property
    def path(self) -> Path | None:
        return self._path

    def _write(self, entry: dict[str, str]) -> None:
        if self._path is not None:
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def record(self, role: str, text: str) -> None:
        """Append one utterance; file I/O runs off the audio event loop."""
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "session": self.session_id,
            "role": role,
            "text": text,
        }
        if self._echo:
            logger.info("[transcript] %s: %s", role, text)
        await asyncio.to_thread(self._write, entry)


class TranscriptLogger(FrameProcessor):
    """Passthrough processor recording one side of the conversation.

    ``side="caller"`` records ``TranscriptionFrame`` (place after STT);
    ``side="agent"`` records ``TTSTextFrame`` (place after TTS, before the
    transport output, so every spoken agent utterance — greeting included —
    is captured).
    """

    def __init__(self, store: TranscriptStore, side: str = "caller") -> None:
        super().__init__()
        if side not in ("caller", "agent"):
            raise ValueError(f"side must be 'caller' or 'agent', got {side!r}")
        self.store = store
        self.side = side

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if self.side == "caller" and isinstance(frame, TranscriptionFrame):
            await self.store.record("caller", frame.text)
        elif self.side == "agent" and isinstance(frame, TTSTextFrame):
            await self.store.record("agent", frame.text)
        await self.push_frame(frame, direction)
