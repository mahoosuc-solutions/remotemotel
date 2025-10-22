"""
Realtime Bridge - Connect Twilio to OpenAI Realtime API

This bridge enables seamless voice conversations by connecting:
Twilio Phone Call ↔ Realtime Bridge ↔ OpenAI Realtime API ↔ Hotel Tools

Features:
- Bidirectional audio streaming
- Function calling integration
- Audio format conversion
- Interruption handling
- Session coordination
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class RealtimeBridge:
    """
    Bridge between Twilio and OpenAI Realtime API

    This is the production-ready blueprint that coordinates:
    1. Receiving audio from Twilio (μ-law)
    2. Converting to PCM16 for Realtime API
    3. Sending audio to Realtime API
    4. Receiving audio responses from Realtime API
    5. Converting back to μ-law
    6. Sending to Twilio
    7. Handling function calls to hotel tools
    """

    def __init__(
        self,
        session_id: str,
        realtime_client: Optional[Any] = None,  # RealtimeAPIClient
        function_registry: Optional[Any] = None,  # FunctionRegistry
        conversation_manager: Optional[Any] = None  # ConversationManager
    ):
        """
        Initialize Realtime bridge

        Args:
            session_id: Voice session ID
            realtime_client: OpenAI Realtime API client
            function_registry: Function registry for tool calls
            conversation_manager: Conversation manager
        """
        self.session_id = session_id
        self.realtime_client = realtime_client
        self.function_registry = function_registry
        self.conversation_manager = conversation_manager

        # Connection state
        self.is_active = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Audio processors
        self.audio_processor = None  # Will be initialized
        self.recording_enabled = True

        # Statistics
        self.twilio_packets_received = 0
        self.twilio_packets_sent = 0
        self.realtime_messages_received = 0
        self.realtime_messages_sent = 0
        self.function_calls_executed = 0

        self.logger = logging.getLogger(f"{__name__}.RealtimeBridge")

    async def start(self) -> None:
        """
        Start the bridge

        Initializes connections and starts audio processing
        """
        self.logger.info(f"Starting Realtime bridge for session {self.session_id}")

        # Initialize audio processor
        from packages.voice.audio import AudioProcessor
        self.audio_processor = AudioProcessor()

        # Connect to Realtime API if not already connected
        if self.realtime_client and not self.realtime_client.is_connected:
            await self.realtime_client.connect()

        # Register event handlers
        if self.realtime_client:
            self._register_realtime_handlers()

        self.is_active = True
        self.start_time = datetime.utcnow()

        self.logger.info("Realtime bridge started")

    async def stop(self) -> None:
        """Stop the bridge"""
        self.is_active = False
        self.end_time = datetime.utcnow()

        # Disconnect from Realtime API
        if self.realtime_client and self.realtime_client.is_connected:
            await self.realtime_client.disconnect()

        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        self.logger.info(f"Realtime bridge stopped after {duration:.2f}s")

    def _register_realtime_handlers(self) -> None:
        """Register event handlers for Realtime API events"""
        if not self.realtime_client:
            return

        # Handle audio output
        self.realtime_client.on(
            "response.audio.delta",
            self._handle_audio_delta
        )

        # Handle transcription
        self.realtime_client.on(
            "response.audio_transcript.done",
            self._handle_transcript
        )

        # Handle function calls
        self.realtime_client.on(
            "response.function_call_arguments.done",
            self._handle_function_call
        )

        # Handle speech detection
        self.realtime_client.on(
            "input_audio_buffer.speech_started",
            self._handle_speech_started
        )

        self.realtime_client.on(
            "input_audio_buffer.speech_stopped",
            self._handle_speech_stopped
        )

    async def process_twilio_audio(self, base64_mulaw: str) -> None:
        """
        Process audio from Twilio

        Args:
            base64_mulaw: Base64-encoded μ-law audio from Twilio
        """
        if not self.is_active:
            return

        self.twilio_packets_received += 1

        try:
            # Decode Twilio audio (μ-law to PCM)
            from packages.voice.audio import decode_twilio_audio

            pcm_audio = decode_twilio_audio(base64_mulaw)

            # Resample from 8kHz to 24kHz if needed for Realtime API
            if self.audio_processor:
                pcm_24k = self.audio_processor.resample(
                    pcm_audio,
                    from_rate=8000,
                    to_rate=24000,
                    sample_width=2
                )
            else:
                pcm_24k = pcm_audio

            # Send to Realtime API
            if self.realtime_client and self.realtime_client.is_connected:
                await self.realtime_client.send_audio(pcm_24k)
                self.realtime_messages_sent += 1

        except Exception as e:
            self.logger.error(f"Error processing Twilio audio: {e}")

    async def send_audio_to_twilio(self, pcm_audio: bytes) -> str:
        """
        Convert and format audio for Twilio

        Args:
            pcm_audio: PCM16 audio bytes (24kHz from Realtime API)

        Returns:
            Base64-encoded μ-law audio for Twilio
        """
        try:
            # Resample from 24kHz to 8kHz for Twilio
            if self.audio_processor:
                pcm_8k = self.audio_processor.resample(
                    pcm_audio,
                    from_rate=24000,
                    to_rate=8000,
                    sample_width=2
                )
            else:
                pcm_8k = pcm_audio

            # Encode to Twilio format (μ-law)
            from packages.voice.audio import encode_twilio_audio

            base64_mulaw = encode_twilio_audio(pcm_8k)
            self.twilio_packets_sent += 1

            return base64_mulaw

        except Exception as e:
            self.logger.error(f"Error sending audio to Twilio: {e}")
            return ""

    async def _handle_audio_delta(self, event: Dict[str, Any]) -> None:
        """
        Handle audio delta from Realtime API

        Args:
            event: Audio delta event
        """
        self.realtime_messages_received += 1

        # Extract audio
        delta = event.get("delta", "")
        if not delta:
            return

        # Decode base64
        import base64
        pcm_audio = base64.b64decode(delta)

        # Convert and send to Twilio
        twilio_audio = await self.send_audio_to_twilio(pcm_audio)

        # TODO: Send to Twilio WebSocket
        # This would be handled by the VoiceGateway

    async def _handle_transcript(self, event: Dict[str, Any]) -> None:
        """
        Handle transcript from Realtime API

        Args:
            event: Transcript event
        """
        transcript = event.get("transcript", "")

        if transcript and self.conversation_manager:
            self.conversation_manager.add_turn(
                role="assistant",
                content=transcript,
                metadata={"source": "realtime_api"}
            )

        self.logger.info(f"Assistant: {transcript}")

    async def _handle_function_call(self, event: Dict[str, Any]) -> None:
        """
        Handle function call from Realtime API

        Args:
            event: Function call event
        """
        call_id = event.get("call_id")
        name = event.get("name")
        arguments_str = event.get("arguments", "{}")

        import json
        arguments = json.loads(arguments_str)

        self.logger.info(f"Function call: {name}({arguments})")
        self.function_calls_executed += 1

        # Execute function
        if self.function_registry:
            try:
                result = await self.function_registry.execute(name, arguments)

                # Send result back to Realtime API
                if self.realtime_client:
                    await self.realtime_client.send_function_result(call_id, result)

            except Exception as e:
                self.logger.error(f"Error executing function {name}: {e}")

                # Send error back
                if self.realtime_client:
                    await self.realtime_client.send_function_error(call_id, str(e))

    async def _handle_speech_started(self, event: Dict[str, Any]) -> None:
        """Handle speech started event (user started talking)"""
        self.logger.debug("User started speaking")

        # Can cancel current AI response if needed (interruption)
        if self.realtime_client and self.realtime_client.is_connected:
            # await self.realtime_client.cancel_response()
            pass  # Optional: handle interruption

    async def _handle_speech_stopped(self, event: Dict[str, Any]) -> None:
        """Handle speech stopped event (user stopped talking)"""
        self.logger.debug("User stopped speaking")

        # Commit audio for processing
        if self.realtime_client and self.realtime_client.is_connected:
            await self.realtime_client.commit_audio()

    async def inject_context(self, context: Dict[str, Any]) -> None:
        """
        Inject context into the conversation

        Args:
            context: Context to inject (hotel info, guest info, etc.)
        """
        if self.realtime_client and self.realtime_client.is_connected:
            # Send context as a system message
            context_message = f"Current context: {json.dumps(context)}"

            # This would be sent as part of conversation
            # Implementation depends on Realtime API specifics
            self.logger.info(f"Injecting context: {list(context.keys())}")

    async def handle_interruption(self) -> None:
        """
        Handle user interruption (barge-in)

        Cancels current response and allows user to speak
        """
        if self.realtime_client and self.realtime_client.is_connected:
            await self.realtime_client.cancel_response()
            self.logger.info("Handled interruption - cancelled current response")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get bridge statistics

        Returns:
            Dict with statistics
        """
        duration = 0.0
        if self.start_time:
            end = self.end_time or datetime.utcnow()
            duration = (end - self.start_time).total_seconds()

        stats = {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "duration_seconds": duration,
            "twilio_packets_received": self.twilio_packets_received,
            "twilio_packets_sent": self.twilio_packets_sent,
            "realtime_messages_received": self.realtime_messages_received,
            "realtime_messages_sent": self.realtime_messages_sent,
            "function_calls_executed": self.function_calls_executed
        }

        # Add Realtime client stats if available
        if self.realtime_client:
            try:
                realtime_stats = self.realtime_client.get_statistics()
                stats["realtime_client"] = realtime_stats
            except:
                pass

        return stats


async def create_realtime_bridge(
    session_id: str,
    hotel_name: str = "Our Hotel",
    hotel_location: str = "Downtown"
) -> RealtimeBridge:
    """
    Create a complete Realtime bridge with all components

    Args:
        session_id: Voice session ID
        hotel_name: Hotel name
        hotel_location: Hotel location

    Returns:
        Configured RealtimeBridge instance
    """
    from packages.voice.realtime import create_realtime_client
    from packages.voice.function_registry import create_hotel_function_registry
    from packages.voice.conversation import create_hotel_conversation_manager

    # Create conversation manager
    conversation_manager = create_hotel_conversation_manager(
        hotel_name=hotel_name,
        location=hotel_location
    )

    # Create function registry
    function_registry = create_hotel_function_registry()

    # Create Realtime client with system instructions
    instructions = conversation_manager.generate_system_instructions()
    realtime_client = create_realtime_client(
        voice="alloy",
        instructions=instructions
    )

    # Register functions with Realtime client
    for schema in function_registry.functions.values():
        realtime_client.register_function(
            name=schema.name,
            func=schema.function,
            description=schema.description,
            parameters=schema.parameters
        )

    # Create bridge
    bridge = RealtimeBridge(
        session_id=session_id,
        realtime_client=realtime_client,
        function_registry=function_registry,
        conversation_manager=conversation_manager
    )

    # Start the bridge
    await bridge.start()

    return bridge
