"""
Twilio-OpenAI Audio Relay

Bidirectional WebSocket proxy that relays audio between:
- Twilio Media Streams (G.711 μ-law, 8kHz)
- OpenAI Realtime API (PCM16, 24kHz)

This is the core component that makes real-time voice conversations work.

Architecture:
    [Caller] <--PSTN--> [Twilio] <--WS1--> [Relay] <--WS2--> [OpenAI]
                                    ▲
                                    │
                              Audio Transcoding
                              μ-law ↔ PCM16
"""

import asyncio
import logging
import base64
from typing import Optional
from fastapi import WebSocket

from packages.voice.realtime import RealtimeAPIClient
from packages.voice.audio import (
    mulaw_decode,
    mulaw_encode,
    resample_audio,
    AudioFormat
)

logger = logging.getLogger(__name__)


class TwilioOpenAIRelay:
    """
    Bidirectional audio relay between Twilio Media Streams and OpenAI Realtime API

    Handles:
    - Audio format conversion (G.711 μ-law ↔ PCM16)
    - Sample rate conversion (8kHz ↔ 24kHz)
    - Bidirectional streaming
    - Connection lifecycle management
    """

    def __init__(
        self,
        twilio_ws: WebSocket,
        openai_client: RealtimeAPIClient,
        call_sid: Optional[str] = None,
        stream_sid: Optional[str] = None
    ):
        """
        Initialize relay

        Args:
            twilio_ws: Twilio Media Stream WebSocket connection
            openai_client: Connected OpenAI Realtime API client
            call_sid: Twilio call SID (for logging)
            stream_sid: Twilio stream SID (for logging)
        """
        self.twilio_ws = twilio_ws
        self.openai = openai_client
        self.call_sid = call_sid or "unknown"
        self.stream_sid = stream_sid or "unknown"

        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.TwilioOpenAIRelay.{self.call_sid}")
        self.logger.info(f"TwilioOpenAIRelay initialized for call {self.call_sid} (stream: {self.stream_sid})")

        # State
        self.active = False
        self.twilio_stream_sid = None

        # Statistics
        self.twilio_packets_received = 0
        self.twilio_packets_sent = 0
        self.openai_chunks_received = 0
        self.openai_chunks_sent = 0

        # Audio buffer for OpenAI -> Twilio
        # Twilio expects 20ms chunks (160 samples at 8kHz)
        self.output_buffer = bytearray()
        self.twilio_chunk_size = 160  # 20ms at 8kHz

        logger.info(f"Relay initialized for call {self.call_sid}")

    async def start(self):
        """
        Start bidirectional audio relay

        Spawns two tasks:
        1. Twilio → OpenAI (inbound audio from caller)
        2. OpenAI → Twilio (outbound audio to caller)
        """
        try:
            self.active = True
            self.logger.info(f"Starting bidirectional audio relay")
            self.logger.debug(f"Relay configuration - Twilio: {self.twilio_format}, OpenAI: {self.openai_format}")

            # Run both directions concurrently
            await asyncio.gather(
                self._relay_twilio_to_openai(),
                self._relay_openai_to_twilio(),
                return_exceptions=True
            )

        except Exception as e:
            self.logger.error(f"Error in relay: {e}", exc_info=True)
        finally:
            self.active = False
            self.logger.info(f"Relay stopped - processed {self.twilio_packets_received} inbound, {self.twilio_packets_sent} outbound packets")

    async def _relay_twilio_to_openai(self):
        """
        Relay audio from Twilio to OpenAI

        Receives G.711 μ-law audio from Twilio Media Stream,
        transcodes to PCM16, resamples to 24kHz, and sends to OpenAI.
        """
        self.logger.info(f"Started Twilio→OpenAI relay")

        try:
            while self.active:
                # Receive message from Twilio
                message = await self.twilio_ws.receive_json()
                event = message.get("event")

                if event == "connected":
                    self.logger.debug(f"Twilio stream connected")

                elif event == "start":
                    # Stream metadata
                    self.twilio_stream_sid = message.get("streamSid")
                    start_data = message.get("start", {})
                    self.logger.info(
                        f"Twilio stream started: {self.twilio_stream_sid} "
                        f"(call: {start_data.get('callSid', 'unknown')})"
                    )

                elif event == "media":
                    # Process incoming audio from caller
                    media = message.get("media", {})
                    payload_b64 = media.get("payload", "")

                    if payload_b64:
                        # Decode base64 → μ-law bytes
                        mulaw_bytes = base64.b64decode(payload_b64)

                        # Transcode μ-law → PCM16
                        pcm16_8khz = mulaw_decode(mulaw_bytes)

                        # Resample 8kHz → 24kHz for OpenAI
                        pcm16_24khz = resample_audio(
                            pcm16_8khz,
                            from_rate=8000,
                            to_rate=24000
                        )

                        # Send to OpenAI
                        await self.openai.send_audio(pcm16_24khz)

                        self.twilio_packets_received += 1
                        self.openai_chunks_sent += 1

                        if self.twilio_packets_received % 100 == 0:
                            self.logger.debug(
                                f"Twilio→OpenAI: {self.twilio_packets_received} packets processed"
                            )

                elif event == "stop":
                    self.logger.info(f"Twilio stream stopped: {self.stream_sid}")
                    self.active = False
                    break

        except Exception as e:
            self.logger.error(
                f"Error in Twilio→OpenAI relay: {e}",
                exc_info=True
            )
            self.active = False

    async def _relay_openai_to_twilio(self):
        """
        Relay audio from OpenAI to Twilio

        Receives PCM16 24kHz audio from OpenAI,
        resamples to 8kHz, transcodes to G.711 μ-law, and sends to Twilio.
        """
        self.logger.info(f"Started OpenAI→Twilio relay")

        try:
            # Listen for audio deltas from OpenAI
            self.openai.on("response.audio.delta", self._handle_openai_audio_delta)

            # Keep connection alive while active
            while self.active:
                await asyncio.sleep(0.1)

                # Flush buffered audio to Twilio
                await self._flush_audio_to_twilio()

        except Exception as e:
            self.logger.error(
                f"Error in OpenAI→Twilio relay: {e}",
                exc_info=True
            )
            self.active = False

    async def _handle_openai_audio_delta(self, event: dict):
        """
        Handle audio delta from OpenAI

        Args:
            event: OpenAI event containing audio delta
        """
        try:
            delta_b64 = event.get("delta", "")
            if not delta_b64:
                return

            # Decode base64 → PCM16 24kHz
            pcm16_24khz = base64.b64decode(delta_b64)

            # Resample 24kHz → 8kHz for Twilio
            pcm16_8khz = resample_audio(
                pcm16_24khz,
                from_rate=24000,
                to_rate=8000
            )

            # Transcode PCM16 → μ-law
            mulaw_bytes = mulaw_encode(pcm16_8khz)

            # Add to buffer (will be sent in chunks)
            self.output_buffer.extend(mulaw_bytes)

            self.openai_chunks_received += 1

        except Exception as e:
            logger.error(f"Error handling OpenAI audio delta: {e}", exc_info=True)

    async def _flush_audio_to_twilio(self):
        """
        Flush buffered audio to Twilio in proper chunk sizes

        Twilio expects 20ms chunks (160 samples at 8kHz).
        We buffer OpenAI audio and send in Twilio-compatible chunks.
        """
        try:
            while len(self.output_buffer) >= self.twilio_chunk_size:
                # Extract one chunk (20ms = 160 samples)
                chunk = bytes(self.output_buffer[:self.twilio_chunk_size])
                self.output_buffer = self.output_buffer[self.twilio_chunk_size:]

                # Encode to base64
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')

                # Send to Twilio
                media_message = {
                    "event": "media",
                    "streamSid": self.twilio_stream_sid,
                    "media": {
                        "payload": chunk_b64
                    }
                }

                await self.twilio_ws.send_json(media_message)

                self.twilio_packets_sent += 1

                if self.twilio_packets_sent % 100 == 0:
                    logger.debug(
                        f"OpenAI→Twilio: {self.twilio_packets_sent} packets"
                    )

        except Exception as e:
            logger.error(f"Error flushing audio to Twilio: {e}", exc_info=True)

    def get_statistics(self) -> dict:
        """
        Get relay statistics

        Returns:
            Dictionary with relay stats
        """
        return {
            "call_sid": self.call_sid,
            "stream_sid": self.stream_sid,
            "active": self.active,
            "twilio_packets_received": self.twilio_packets_received,
            "twilio_packets_sent": self.twilio_packets_sent,
            "openai_chunks_received": self.openai_chunks_received,
            "openai_chunks_sent": self.openai_chunks_sent,
            "buffer_size": len(self.output_buffer)
        }

    async def stop(self):
        """Stop the relay gracefully"""
        logger.info(f"Stopping relay for call {self.call_sid}")
        self.active = False

        # Send any remaining buffered audio
        await self._flush_audio_to_twilio()

        # Log final statistics
        stats = self.get_statistics()
        logger.info(f"Relay statistics for call {self.call_sid}: {stats}")


async def create_relay(
    twilio_ws: WebSocket,
    openai_client: RealtimeAPIClient,
    call_sid: Optional[str] = None,
    stream_sid: Optional[str] = None
) -> TwilioOpenAIRelay:
    """
    Create and start a Twilio-OpenAI audio relay

    Args:
        twilio_ws: Twilio Media Stream WebSocket
        openai_client: Connected OpenAI Realtime API client
        call_sid: Twilio call SID
        stream_sid: Twilio stream SID

    Returns:
        Running TwilioOpenAIRelay instance
    """
    relay = TwilioOpenAIRelay(twilio_ws, openai_client, call_sid, stream_sid)
    await relay.start()
    return relay
