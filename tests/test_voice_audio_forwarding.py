import base64

import pytest

from voice_ai_server import build_twilio_audio_event


def test_build_twilio_audio_event_happy_path():
    stream_sid = "MZ123"
    raw_audio = b"\x00\x01\x02\x03"
    delta = base64.b64encode(raw_audio).decode("utf-8")

    event = build_twilio_audio_event(stream_sid, delta)

    assert event == {
        "event": "media",
        "streamSid": stream_sid,
        "media": {
            "payload": base64.b64encode(raw_audio).decode("utf-8")
        }
    }


def test_build_twilio_audio_event_requires_stream_sid():
    raw_audio = b"\x04\x05"
    delta = base64.b64encode(raw_audio).decode("utf-8")

    assert build_twilio_audio_event(None, delta) is None


def test_build_twilio_audio_event_invalid_payload():
    with pytest.raises(ValueError):
        build_twilio_audio_event("MZ123", "!!!not-base64!!!")
