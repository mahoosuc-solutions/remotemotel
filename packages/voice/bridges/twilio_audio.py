"""
Twilio Audio Bridge

Integrates Twilio media streams with audio processing pipeline:
- Receives Twilio audio (base64 μ-law)
- Processes with STT
- Generates responses with TTS
- Sends back to Twilio
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AudioStreamMessage:
    """Represents a message in the audio stream"""
    event: str  # 'connected', 'start', 'media', 'stop'
    stream_sid: Optional[str] = None
    call_sid: Optional[str] = None
    payload: Optional[str] = None  # base64 audio
    sequence_number: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class TwilioAudioBridge:
    """
    Bridge between Twilio media streams and audio processing

    Handles:
    - Receiving Twilio audio streams
    - Buffering and chunking audio
    - STT transcription
    - TTS synthesis
    - Sending audio back to Twilio
    """

    def __init__(
        self,
        session_id: str,
        on_transcription: Optional[Callable[[str], Any]] = None,
        on_audio_received: Optional[Callable[[bytes], Any]] = None
    ):
        """
        Initialize Twilio audio bridge

        Args:
            session_id: Voice session identifier
            on_transcription: Callback when text is transcribed
            on_audio_received: Callback when audio chunk is received
        """
        self.session_id = session_id
        self.on_transcription = on_transcription
        self.on_audio_received = on_audio_received

        # Stream state
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.is_active = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Audio buffering
        self.audio_buffer = bytearray()
        self.buffer_size_ms = 1000  # Buffer 1 second of audio before processing
        self.sample_rate = 8000  # Twilio uses 8kHz μ-law

        # Statistics
        self.packets_received = 0
        self.packets_sent = 0
        self.bytes_received = 0
        self.bytes_sent = 0

        self.logger = logging.getLogger(f"{__name__}.TwilioAudioBridge")
        self.logger.info(f"TwilioAudioBridge initialized for session {session_id}")

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle incoming Twilio media stream message

        Args:
            message: Twilio WebSocket message

        Returns:
            Response message to send back (if any)
        """
        event = message.get("event")

        if event == "connected":
            return await self._handle_connected(message)

        elif event == "start":
            return await self._handle_start(message)

        elif event == "media":
            return await self._handle_media(message)

        elif event == "stop":
            return await self._handle_stop(message)

        else:
            self.logger.warning(f"Unknown event: {event}")
            return None

    async def _handle_connected(self, message: Dict[str, Any]) -> None:
        """Handle stream connected event"""
        self.logger.info("Twilio media stream connected")
        return None

    async def _handle_start(self, message: Dict[str, Any]) -> None:
        """Handle stream start event"""
        start_data = message.get("start", {})
        self.stream_sid = message.get("streamSid")
        self.call_sid = start_data.get("callSid")
        self.is_active = True
        self.start_time = datetime.utcnow()

        self.logger.info(
            f"Audio stream started - Stream: {self.stream_sid}, Call: {self.call_sid}"
        )

        return None

    async def _handle_media(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle incoming audio data

        Args:
            message: Media message with audio payload

        Returns:
            Response to send (if any)
        """
        media_data = message.get("media", {})
        payload = media_data.get("payload")  # base64 μ-law audio
        sequence_number = media_data.get("sequence")

        if not payload:
            return None

        self.packets_received += 1

        # Decode audio (imported at runtime to avoid circular imports)
        from packages.voice.audio import decode_twilio_audio

        try:
            # Decode from base64 μ-law to PCM
            pcm_audio = decode_twilio_audio(payload)
            self.bytes_received += len(pcm_audio)

            # Add to buffer
            self.audio_buffer.extend(pcm_audio)

            # Callback for raw audio
            if self.on_audio_received:
                await self._safe_callback(self.on_audio_received, pcm_audio)

            # Check if buffer is large enough to process
            buffer_threshold = int(self.sample_rate * 2 * self.buffer_size_ms / 1000)

            if len(self.audio_buffer) >= buffer_threshold:
                await self._process_audio_buffer()

        except Exception as e:
            self.logger.error(f"Error processing media: {e}", exc_info=True)

        return None

    async def _handle_stop(self, message: Dict[str, Any]) -> None:
        """Handle stream stop event"""
        self.is_active = False
        self.end_time = datetime.utcnow()

        # Process any remaining audio in buffer
        if len(self.audio_buffer) > 0:
            await self._process_audio_buffer()

        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0

        self.logger.info(
            f"Audio stream stopped - Duration: {duration:.2f}s, "
            f"Packets received: {self.packets_received}, "
            f"Bytes received: {self.bytes_received}"
        )

        return None

    async def _process_audio_buffer(self) -> None:
        """Process accumulated audio buffer (transcribe)"""
        if len(self.audio_buffer) == 0:
            return

        # Get audio data
        audio_data = bytes(self.audio_buffer)
        self.audio_buffer.clear()

        # Transcribe (if STT is available)
        try:
            from packages.voice.audio import detect_speech

            # Check if there's speech
            has_speech = detect_speech(audio_data, self.sample_rate)

            if has_speech:
                self.logger.debug(f"Speech detected, transcribing {len(audio_data)} bytes")

                # Transcribe would happen here
                # For now, just log
                # In Phase 3, integrate with STT engine:
                # from packages.voice.stt import transcribe_audio
                # text = await transcribe_audio(audio_data)

                text = "[Transcription placeholder]"

                # Callback with transcription
                if self.on_transcription:
                    await self._safe_callback(self.on_transcription, text)

            else:
                self.logger.debug("No speech detected in buffer")

        except Exception as e:
            self.logger.error(f"Error processing audio buffer: {e}")

    async def send_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Send audio back to Twilio

        Args:
            audio_data: PCM audio bytes to send

        Returns:
            Media message for Twilio
        """
        from packages.voice.audio import encode_twilio_audio

        try:
            # Encode PCM to base64 μ-law
            payload = encode_twilio_audio(audio_data)

            # Create media message
            message = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {
                    "payload": payload
                }
            }

            self.packets_sent += 1
            self.bytes_sent += len(audio_data)

            return message

        except Exception as e:
            self.logger.error(f"Error sending audio: {e}")
            raise

    async def send_tts(self, text: str, voice: str = "alloy") -> None:
        """
        Synthesize text and send to Twilio

        Args:
            text: Text to speak
            voice: TTS voice to use
        """
        try:
            # Synthesize speech
            # In Phase 3, use real TTS:
            # from packages.voice.tts import synthesize_speech
            # audio_data = await synthesize_speech(text, voice)

            # For now, just log
            self.logger.info(f"TTS: '{text}' (voice: {voice})")

            # Would send audio here:
            # await self.send_audio(audio_data)

        except Exception as e:
            self.logger.error(f"Error in TTS: {e}")

    async def _safe_callback(self, callback: Callable, *args, **kwargs) -> None:
        """
        Safely execute callback with error handling

        Args:
            callback: Callback function
            *args: Callback arguments
            **kwargs: Callback keyword arguments
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in callback: {e}", exc_info=True)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get stream statistics

        Returns:
            Dict with stream stats
        """
        duration = 0.0
        if self.start_time:
            end = self.end_time or datetime.utcnow()
            duration = (end - self.start_time).total_seconds()

        return {
            "session_id": self.session_id,
            "stream_sid": self.stream_sid,
            "call_sid": self.call_sid,
            "is_active": self.is_active,
            "duration_seconds": duration,
            "packets_received": self.packets_received,
            "packets_sent": self.packets_sent,
            "bytes_received": self.bytes_received,
            "bytes_sent": self.bytes_sent,
            "buffer_size": len(self.audio_buffer)
        }


# Factory function
def create_twilio_bridge(
    session_id: str,
    on_transcription: Optional[Callable[[str], Any]] = None
) -> TwilioAudioBridge:
    """
    Create a Twilio audio bridge

    Args:
        session_id: Voice session ID
        on_transcription: Callback for transcriptions

    Returns:
        TwilioAudioBridge instance
    """
    return TwilioAudioBridge(
        session_id=session_id,
        on_transcription=on_transcription
    )
