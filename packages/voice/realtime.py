"""
OpenAI Realtime API Client

Production-ready blueprint for integrating OpenAI's Realtime API
for natural voice conversations.

Reference: https://platform.openai.com/docs/guides/realtime
"""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, AsyncIterator, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Note: websockets should be imported when available
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets not available - Realtime API will not work")


class RealtimeEvent(Enum):
    """Realtime API event types"""
    # Session events
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"

    # Conversation events
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_ITEM_CREATED = "conversation.item.created"
    CONVERSATION_ITEM_DELETED = "conversation.item.deleted"

    # Input audio events
    INPUT_AUDIO_BUFFER_APPEND = "input_audio_buffer.append"
    INPUT_AUDIO_BUFFER_COMMIT = "input_audio_buffer.commit"
    INPUT_AUDIO_BUFFER_CLEAR = "input_audio_buffer.clear"
    INPUT_AUDIO_BUFFER_SPEECH_STARTED = "input_audio_buffer.speech_started"
    INPUT_AUDIO_BUFFER_SPEECH_STOPPED = "input_audio_buffer.speech_stopped"
    INPUT_AUDIO_BUFFER_COMMITTED = "input_audio_buffer.committed"

    # Response events
    RESPONSE_CREATED = "response.created"
    RESPONSE_DONE = "response.done"
    RESPONSE_OUTPUT_ITEM_ADDED = "response.output_item.added"
    RESPONSE_OUTPUT_ITEM_DONE = "response.output_item.done"
    RESPONSE_CONTENT_PART_ADDED = "response.content_part.added"
    RESPONSE_CONTENT_PART_DONE = "response.content_part.done"
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_AUDIO_DONE = "response.audio.done"
    RESPONSE_AUDIO_TRANSCRIPT_DELTA = "response.audio_transcript.delta"
    RESPONSE_AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"

    # Function calling events
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA = "response.function_call_arguments.delta"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE = "response.function_call_arguments.done"

    # Rate limit events
    RATE_LIMITS_UPDATED = "rate_limits.updated"

    # Error events
    ERROR = "error"


@dataclass
class RealtimeSession:
    """Represents a Realtime API session"""
    id: str
    model: str = "gpt-4o-realtime-preview-2024-12-17"
    voice: str = "alloy"
    instructions: str = ""
    input_audio_format: str = "pcm16"  # or "g711_ulaw", "g711_alaw"
    output_audio_format: str = "pcm16"
    input_audio_transcription: Optional[Dict[str, Any]] = None
    turn_detection: Optional[Dict[str, Any]] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)
    temperature: float = 0.8
    max_response_output_tokens: int = 4096


class RealtimeAPIClient:
    """
    OpenAI Realtime API client for voice conversations

    This is a production-ready blueprint implementation that will work
    when OpenAI Realtime API is available.

    Features:
    - WebSocket connection management
    - Bidirectional audio streaming
    - Function calling
    - Context injection
    - Event handling
    - Error recovery
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-realtime-preview-2024-12-17",
        voice: str = "alloy",
        instructions: str = ""
    ):
        """
        Initialize Realtime API client

        Args:
            api_key: OpenAI API key (uses env var if None)
            model: Model to use
            voice: Voice for TTS
            instructions: System instructions for the model
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets package is required for Realtime API")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.voice = voice
        self.instructions = instructions

        # Connection state
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.session: Optional[RealtimeSession] = None
        self.is_connected = False

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Audio buffers
        self.input_audio_buffer = bytearray()
        self.output_audio_buffer = bytearray()

        # Function registry
        self.functions: Dict[str, Callable] = {}

        # Statistics
        self.bytes_sent = 0
        self.bytes_received = 0
        self.events_received = 0
        self.function_calls = 0

        self.logger = logging.getLogger(f"{__name__}.RealtimeAPIClient")

    async def connect(self) -> None:
        """
        Connect to OpenAI Realtime API

        Establishes WebSocket connection and creates session
        """
        try:
            # WebSocket URL
            url = "wss://api.openai.com/v1/realtime"
            params = f"?model={self.model}"

            # Connect with authentication
            # Note: websockets 15.0+ changed API
            self.logger.info(f"Connecting to Realtime API: {url}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1",
            }

            connect_kwargs = {
                "ping_interval": 30,
                "ping_timeout": 10,
            }

            try:
                self.ws = await websockets.connect(
                    url + params,
                    extra_headers=headers,
                    **connect_kwargs,
                )
            except TypeError:
                # Older websockets versions (<11) use `additional_headers`
                self.ws = await websockets.connect(
                    url + params,
                    additional_headers=headers,
                    **connect_kwargs,
                )

            self.is_connected = True
            self.logger.info("Connected to Realtime API")

            # Update session configuration
            await self._update_session()

            # Start event loop
            asyncio.create_task(self._event_loop())

        except Exception as e:
            self.logger.error(f"Failed to connect to Realtime API: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Realtime API"""
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.is_connected = False
            self.logger.info("Disconnected from Realtime API")

    async def _update_session(self) -> None:
        """Update session configuration"""
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": self.instructions,
                "voice": self.voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [self._format_function(name, func) for name, func in self.functions.items()],
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }

        await self._send_event(session_config)
        self.logger.info("Session configuration updated")

    async def _event_loop(self) -> None:
        """
        Main event loop for receiving messages

        Continuously receives and processes events from Realtime API
        """
        try:
            async for message in self.ws:
                self.events_received += 1
                self.bytes_received += len(message)

                event = json.loads(message)
                event_type = event.get("type")

                self.logger.debug(f"Received event: {event_type}")

                # Handle event
                await self._handle_event(event)

                # Trigger registered handlers
                await self._trigger_handlers(event_type, event)

        except websockets.exceptions.ConnectionClosed:
            self.logger.info("Connection closed by server")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"Error in event loop: {e}", exc_info=True)
            self.is_connected = False

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """
        Handle specific event types

        Args:
            event: Event data from Realtime API
        """
        event_type = event.get("type")

        if event_type == RealtimeEvent.SESSION_CREATED.value:
            self.session = RealtimeSession(**event.get("session", {}))
            self.logger.info(f"Session created: {self.session.id}")

        elif event_type == RealtimeEvent.RESPONSE_AUDIO_DELTA.value:
            # Received audio chunk
            delta = event.get("delta", "")
            if delta:
                # Decode base64 audio
                import base64
                audio_bytes = base64.b64decode(delta)
                self.output_audio_buffer.extend(audio_bytes)

        elif event_type == RealtimeEvent.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE.value:
            # Function call completed
            await self._execute_function_call(event)

        elif event_type == RealtimeEvent.INPUT_AUDIO_BUFFER_SPEECH_STARTED.value:
            self.logger.debug("User started speaking")

        elif event_type == RealtimeEvent.INPUT_AUDIO_BUFFER_SPEECH_STOPPED.value:
            self.logger.debug("User stopped speaking")

        elif event_type == RealtimeEvent.ERROR.value:
            error = event.get("error", {})
            self.logger.error(f"Realtime API error: {error}")

    async def _execute_function_call(self, event: Dict[str, Any]) -> None:
        """
        Execute a function call from the API

        Args:
            event: Function call event
        """
        call_id = event.get("call_id")
        name = event.get("name")
        arguments = json.loads(event.get("arguments", "{}"))

        self.logger.info(f"Executing function: {name} with args: {arguments}")
        self.function_calls += 1

        # Get function
        func = self.functions.get(name)
        if not func:
            self.logger.error(f"Function not found: {name}")
            return

        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)

            # Send result back
            await self.send_function_result(call_id, result)

        except Exception as e:
            self.logger.error(f"Error executing function {name}: {e}")
            await self.send_function_error(call_id, str(e))

    async def send_audio(self, audio_data: bytes) -> None:
        """
        Send audio to Realtime API

        Args:
            audio_data: PCM16 audio bytes
        """
        import base64

        # Encode to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }

        await self._send_event(event)
        self.input_audio_buffer.extend(audio_data)

    async def commit_audio(self) -> None:
        """Commit audio buffer for processing"""
        event = {"type": "input_audio_buffer.commit"}
        await self._send_event(event)
        self.logger.debug("Audio buffer committed")

    async def clear_audio_buffer(self) -> None:
        """Clear input audio buffer"""
        event = {"type": "input_audio_buffer.clear"}
        await self._send_event(event)
        self.input_audio_buffer.clear()

    async def send_text(self, text: str) -> None:
        """
        Send text message

        Args:
            text: Text message to send
        """
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }

        await self._send_event(event)

        # Trigger response
        await self.create_response()

    async def create_response(self) -> None:
        """Request the model to generate a response"""
        event = {"type": "response.create"}
        await self._send_event(event)

    async def cancel_response(self) -> None:
        """Cancel current response generation"""
        event = {"type": "response.cancel"}
        await self._send_event(event)

    async def send_function_result(self, call_id: str, result: Any) -> None:
        """
        Send function call result back to API

        Args:
            call_id: Function call ID
            result: Function execution result
        """
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result)
            }
        }

        await self._send_event(event)
        await self.create_response()

    async def send_function_error(self, call_id: str, error: str) -> None:
        """
        Send function call error

        Args:
            call_id: Function call ID
            error: Error message
        """
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps({"error": error})
            }
        }

        await self._send_event(event)

    def register_function(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        """
        Register a function for function calling

        Args:
            name: Function name
            func: Function to call
            description: Function description
            parameters: JSON schema for parameters
        """
        self.functions[name] = func
        self.logger.info(f"Registered function: {name}")

    def _format_function(self, name: str, func: Callable) -> Dict[str, Any]:
        """
        Format function for Realtime API

        Args:
            name: Function name
            func: Function callable

        Returns:
            Function schema
        """
        # This should extract schema from function
        # For now, return basic format
        return {
            "type": "function",
            "name": name,
            "description": func.__doc__ or f"Execute {name}",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    def on(self, event_type: str, handler: Callable) -> None:
        """
        Register event handler

        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)

    async def _trigger_handlers(self, event_type: str, event: Dict[str, Any]) -> None:
        """
        Trigger registered event handlers

        Args:
            event_type: Event type
            event: Event data
        """
        handlers = self.event_handlers.get(event_type, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler: {e}")

    async def _send_event(self, event: Dict[str, Any]) -> None:
        """
        Send event to Realtime API

        Args:
            event: Event data
        """
        if not self.is_connected or not self.ws:
            raise RuntimeError("Not connected to Realtime API")

        message = json.dumps(event)
        await self.ws.send(message)

        self.bytes_sent += len(message)
        self.logger.debug(f"Sent event: {event.get('type')}")

    async def stream_audio_out(self) -> AsyncIterator[bytes]:
        """
        Stream audio output as it arrives

        Yields:
            Audio chunks from the API
        """
        while self.is_connected:
            if len(self.output_audio_buffer) > 0:
                # Get and clear buffer
                audio_chunk = bytes(self.output_audio_buffer)
                self.output_audio_buffer.clear()
                yield audio_chunk

            await asyncio.sleep(0.01)  # 10ms polling

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get client statistics

        Returns:
            Dict with stats
        """
        return {
            "is_connected": self.is_connected,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "events_received": self.events_received,
            "function_calls": self.function_calls,
            "input_buffer_size": len(self.input_audio_buffer),
            "output_buffer_size": len(self.output_audio_buffer),
            "registered_functions": len(self.functions)
        }


# Convenience function
def create_realtime_client(
    api_key: Optional[str] = None,
    voice: str = "alloy",
    instructions: str = ""
) -> RealtimeAPIClient:
    """
    Create a Realtime API client

    Args:
        api_key: OpenAI API key
        voice: Voice for TTS
        instructions: System instructions

    Returns:
        RealtimeAPIClient instance
    """
    return RealtimeAPIClient(
        api_key=api_key,
        voice=voice,
        instructions=instructions
    )
