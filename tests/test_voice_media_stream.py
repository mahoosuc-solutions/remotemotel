import asyncio
import base64
import json
from types import SimpleNamespace

import pytest

import voice_ai_server


class DummyTwilioWebSocket:
    """Minimal FastAPI WebSocket stand-in for testing the media bridge."""

    def __init__(self, messages):
        self._messages = list(messages)
        self.sent_messages = []
        self.accepted = False
        self.closed = None

    @property
    def headers(self):
        return {}

    async def accept(self):
        self.accepted = True

    def iter_text(self):
        async def generator():
            for payload in self._messages:
                yield json.dumps(payload)
        return generator()

    async def send_json(self, payload):
        self.sent_messages.append(payload)

    async def close(self, code=None, reason=None):
        self.closed = (code, reason)


class DummyOpenAIConnection:
    """Stub OpenAI WebSocket used to simulate realtime responses for tests."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.sent_messages = []
        self.state = SimpleNamespace(name="OPEN")

    async def send(self, message):
        self.sent_messages.append(json.loads(message))

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._responses:
            raise StopAsyncIteration
        next_event = self._responses[0]
        if next_event.get("type") == "response.output_audio.delta":
            # Wait until Twilio audio has been forwarded to OpenAI
            for _ in range(500):
                if any(msg["type"] == "input_audio_buffer.append" for msg in self.sent_messages):
                    break
                await asyncio.sleep(0)
            else:  # pragma: no cover - indicates test setup failed
                raise AssertionError("Twilio audio was never forwarded to OpenAI")
        return json.dumps(self._responses.pop(0))

    async def close(self):
        self.state.name = "CLOSED"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


@pytest.mark.asyncio
async def test_media_stream_forwards_openai_audio(monkeypatch):
    delta_audio = base64.b64encode(b"\x00\x11\x22\x33").decode("utf-8")
    openai_responses = [
        {"type": "session.updated"},
        {"type": "response.output_audio.delta", "delta": delta_audio},
    ]
    dummy_openai = DummyOpenAIConnection(openai_responses)

    def fake_connect(*args, **kwargs):
        return dummy_openai

    # Inject fake OpenAI connection and required configuration
    monkeypatch.setattr(voice_ai_server.websockets, "connect", fake_connect)
    monkeypatch.setattr(voice_ai_server, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(voice_ai_server, "OPENAI_REALTIME_MODEL", "dummy-model")
    monkeypatch.setattr(voice_ai_server, "TEMPERATURE", 0.1)

    twilio_messages = [
        {"event": "start", "start": {"streamSid": "MZ123"}},
        {"event": "media", "media": {"payload": base64.b64encode(b"\xaa\xbb\xcc\xdd").decode("utf-8")}},
        {"event": "stop"},
    ]
    twilio_ws = DummyTwilioWebSocket(twilio_messages)

    await voice_ai_server.handle_media_stream(twilio_ws)

    assert twilio_ws.accepted is True
    assert len(twilio_ws.sent_messages) >= 2

    media_message = twilio_ws.sent_messages[0]
    mark_message = twilio_ws.sent_messages[1]

    assert media_message["event"] == "media"
    assert media_message["streamSid"] == "MZ123"
    assert base64.b64decode(media_message["media"]["payload"]) == base64.b64decode(delta_audio)

    assert mark_message["event"] == "mark"
    assert mark_message["streamSid"] == "MZ123"

    sent_types = [msg["type"] for msg in dummy_openai.sent_messages]
    assert "session.update" in sent_types
    assert "input_audio_buffer.append" in sent_types


@pytest.mark.asyncio
async def test_media_stream_requires_api_key(monkeypatch):
    """Voice websocket should close immediately when API key is missing."""
    monkeypatch.setattr(voice_ai_server, "OPENAI_API_KEY", None)

    twilio_ws = DummyTwilioWebSocket([])

    await voice_ai_server.handle_media_stream(twilio_ws)

    assert twilio_ws.accepted is True
    assert twilio_ws.closed == (1008, "OpenAI API key not configured")
    assert twilio_ws.sent_messages == []


@pytest.mark.asyncio
async def test_send_session_update_includes_hotel_context(monkeypatch):
    """Session update payload should include hotel-specific instructions and tools."""
    monkeypatch.setattr(voice_ai_server, "SYSTEM_MESSAGE", "Hotel Instructions Placeholder")
    monkeypatch.setattr(voice_ai_server, "VOICE", "test-voice")

    dummy_openai = DummyOpenAIConnection([])
    await voice_ai_server.send_session_update(dummy_openai)

    assert dummy_openai.sent_messages, "Expected session update to be sent to OpenAI"

    payload = dummy_openai.sent_messages[0]
    assert payload["type"] == "session.update"

    session_config = payload["session"]
    assert session_config["voice"] == "test-voice"
    assert session_config["instructions"] == "Hotel Instructions Placeholder"
    assert session_config["modalities"] == ["text", "audio"]

    tool_names = [tool["name"] for tool in session_config["tools"]]
    assert "check_room_availability" in tool_names
    assert "get_hotel_info" in tool_names
    assert "transfer_to_department" in tool_names
