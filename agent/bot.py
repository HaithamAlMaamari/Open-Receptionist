"""Milestone 1 entry point: browser-mic voice demo.

Run ``python -m agent.bot`` (or ``docker compose up``) and open
http://localhost:7860/client to talk to the receptionist.

Compliance defaults enforced here:
1. The greeting always discloses the agent is an AI assistant (prompt files),
   spoken verbatim so the disclosure cannot be paraphrased away.
2. The greeting and system prompt always offer a path to a human.
3. Both sides of the conversation are transcript-logged (pipeline loggers).
"""

from __future__ import annotations

import logging
from typing import Any

from dotenv import load_dotenv

from agent.config import load_business_config
from agent.pipeline import build_pipeline
from agent.prompt_loader import render_greetings
from agent.transports.webrtc import transport_params

load_dotenv(override=False)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("open_receptionist.bot")


async def run_bot(transport: Any) -> Any:
    """Build and run one voice session on the given transport.

    Returns the pipeline worker (useful for tests and introspection).
    """
    from pipecat.frames.frames import TTSSpeakFrame
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineWorker

    config = load_business_config()
    logger.info("Loaded business config for %s / %s", config.name_en, config.name_ar)

    built = build_pipeline(transport, config)
    worker = PipelineWorker(built.pipeline, params=PipelineParams(enable_metrics=True))

    # One frame per language: a multilingual TTS voice handles separate
    # utterances far better than one mixed-script string. Spoken verbatim
    # (not LLM-generated) so the AI disclosure is guaranteed word-for-word.
    greetings = render_greetings(config)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport: Any, client: Any) -> None:
        logger.info("Client connected — sending greetings (%d languages)", len(greetings))
        await worker.queue_frames([TTSSpeakFrame(text) for text in greetings])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport: Any, client: Any) -> None:
        logger.info("Client disconnected — ending session")
        await worker.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(worker)
    return worker


async def bot(runner_args: Any) -> None:
    """Entry point discovered by the Pipecat dev runner."""
    from pipecat.runner.utils import create_transport

    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
