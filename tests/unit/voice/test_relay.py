from unittest.mock import AsyncMock

from fastapi import WebSocket

from packages.voice.audio import AudioCodec
from packages.voice.relay import TwilioOpenAIRelay


def test_relay_initializes_audio_formats():
    websocket = AsyncMock(spec=WebSocket)
    openai_client = AsyncMock()

    relay = TwilioOpenAIRelay(
        twilio_ws=websocket,
        openai_client=openai_client,
        call_sid="CA123",
        stream_sid="M123",
    )

    assert relay.twilio_format.codec == AudioCodec.MULAW
    assert relay.twilio_format.sample_rate == 8000
    assert relay.openai_format.codec == AudioCodec.PCM
    assert relay.openai_format.sample_rate == 24000
