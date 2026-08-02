"""Browser (SmallWebRTC) transport configuration for local development.

The Pipecat dev runner serves a prebuilt client at http://localhost:7860/client
— open it, click connect, and talk to the agent with your mic.
"""

from __future__ import annotations

from typing import Any


def webrtc_transport_params() -> Any:
    """TransportParams for the SmallWebRTC (browser mic) transport."""
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.transports.base_transport import TransportParams

    return TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    )


# Factory mapping consumed by pipecat.runner.utils.create_transport().
transport_params = {
    "webrtc": webrtc_transport_params,
}
