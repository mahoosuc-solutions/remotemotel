import asyncio
import base64

import pytest

from packages.voice.relay import TwilioOpenAIRelay


class FakeTwilioWebSocket:
    """Minimal Twilio websocket stub for exercising the relay."""

    def __init__(self, events):
        self._queue = asyncio.Queue()
        for event in events:
            self._queue.put_nowait(event)
        self.sent_messages = []

    @property
    def headers(self):
        return {}

    async def receive_json(self):
        return await self._queue.get()

    async def send_json(self, payload):
        self.sent_messages.append(payload)

    def add_event(self, event):
        self._queue.put_nowait(event)


class FakeRealtimeClient:
    """Stub Realtime client that records audio and handlers."""

    def __init__(self):
        self.handlers = {}
        self.audio_payloads = []
        self.is_connected = True

    async def connect(self):
        self.is_connected = True

    async def disconnect(self):
        self.is_connected = False

    def on(self, event_name, handler):
        self.handlers.setdefault(event_name, []).append(handler)

    async def send_audio(self, pcm_bytes):
        self.audio_payloads.append(pcm_bytes)

    async def emit(self, event_name, payload):
        for handler in self.handlers.get(event_name, []):
            result = handler(payload)
            if asyncio.iscoroutine(result):
                await result

    async def send_function_result(self, call_id, result):  # pragma: no cover - not used here
        pass

    async def send_function_error(self, call_id, error):  # pragma: no cover - not used here
        pass


@pytest.mark.asyncio
async def test_twilio_relay_streams_audio_both_directions():
    stream_sid = "MZ123"
    call_sid = "CA123"

    caller_audio = base64.b64encode(bytes([0x7F] * 160)).decode()
    twilio_events = [
        {"event": "start", "streamSid": stream_sid, "start": {"streamSid": stream_sid, "callSid": call_sid}},
        {"event": "media", "streamSid": stream_sid, "media": {"payload": caller_audio}},
    ]

    fake_twilio_ws = FakeTwilioWebSocket(twilio_events)
    fake_openai = FakeRealtimeClient()

    relay = TwilioOpenAIRelay(
        twilio_ws=fake_twilio_ws,
        openai_client=fake_openai,
        call_sid=call_sid,
        stream_sid=stream_sid,
    )

    task = asyncio.create_task(relay.start())

    for _ in range(20):
        if fake_openai.audio_payloads:
            break
        await asyncio.sleep(0.05)
    else:
        pytest.fail("Relay did not forward caller audio to OpenAI client")

    pcm24 = bytes((i % 256 for i in range(960)))
    await fake_openai.emit(
        "response.audio.delta",
        {"delta": base64.b64encode(pcm24).decode()},
    )

    for _ in range(20):
        if any(msg["event"] == "media" for msg in fake_twilio_ws.sent_messages):
            break
        await asyncio.sleep(0.05)

    fake_twilio_ws.add_event({"event": "stop", "streamSid": stream_sid})

    await task

    media_events = [msg for msg in fake_twilio_ws.sent_messages if msg["event"] == "media"]

    assert media_events, "Expected relay to send audio media back to Twilio"
    assert media_events[0]["streamSid"] == stream_sid
    assert fake_openai.audio_payloads, "Expected relay to forward caller audio to OpenAI"
